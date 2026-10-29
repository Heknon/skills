"""The pure parts: verdicts, log reading, stop codes, screenshots, grouping, conclusions."""

from __future__ import annotations

import asyncio
import io
import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from PIL import Image
from pyVmomi import vmodl

from vsphere_mcp import ages, checks, console, contention, diagnose, formatting, scan, vmlog
from vsphere_mcp.config import Settings, Thresholds, VCenter
from vsphere_mcp.inventory import FolderFacts, Inventory, Question, VmFacts, find_environment, os_family
from vsphere_mcp.readonly import ALLOWED_METHODS, ReadOnlyStub, ReadOnlyViolationError, ensure_read_request
from vsphere_mcp.vcenter import VCenterSession
from vsphere_mcp.vrops import Vrops

NOW = datetime(2026, 10, 29, 2, 30, tzinfo=UTC)
LIMITS = Thresholds()


def vm(**fields: object) -> VmFacts:
    base: dict[str, object] = {
        "vcenter": "vc-a",
        "moref": "vm-1",
        "name": "web-01",
        "power_state": "poweredOn",
        "connection_state": "connected",
        "uptime_minutes": 25.0,
        "tools_running": "guestToolsNotRunning",
        "heartbeat": "gray",
        "cpu_mhz": 30.0,
        "num_cpu": 2,
        "host_core_mhz": 2000.0,
        "host": "esx-1",
    }
    base.update(fields)
    return VmFacts(**base)  # type: ignore[arg-type]


# -- configuration ----------------------------------------------------------------


def test_a_vcenter_answers_to_its_name_host_short_host_and_aliases() -> None:
    vcenter = VCenter(name="vc-04", host="vc04.lab.example", aliases=("Datacenter-4",))

    assert all(
        vcenter.answers_to(name)
        for name in ("vc-04", "VC04.lab.example", "vc04", "datacenter-4", "vc04.other")
    )
    assert not vcenter.answers_to("vc-05")


def test_settings_read_vcenters_and_thresholds_from_json() -> None:
    settings = Settings.from_environment(
        {
            "VSPHERE_VCENTERS": (
                '[{"name": "vc-a", "host": "a.example"}, {"name": "vc-b", "host": "b.example", "port": 8443}]'
            ),
            "VSPHERE_USERNAME": "reader",
            "VSPHERE_PASSWORD": "secret",
            "VSPHERE_THRESHOLDS": '{"booted_not_up_minutes": 15}',
            "VSPHERE_ENV_PARENT_HINTS": "environments, projects",
        }
    )

    assert [vcenter.port for vcenter in settings.vcenters] == [443, 8443]
    assert settings.thresholds.booted_not_up_minutes == 15
    assert settings.thresholds.hung_cpu_mhz == 100
    assert settings.env_parent_hints == ("environments", "projects")
    assert settings.vcenter("b").name == "vc-b"
    assert "secret" not in repr(settings)


def test_settings_refuse_a_vcenter_without_credentials_by_variable_name() -> None:
    with pytest.raises(ValueError, match="VSPHERE_"):
        Settings.from_environment({"VSPHERE_VCENTERS": '[{"name": "vc-a", "host": "a"}]'})


def test_an_unknown_vcenter_lists_the_known_ones() -> None:
    settings = Settings.from_environment(
        {
            "VSPHERE_VCENTERS": '[{"name": "vc-a", "host": "a"}]',
            "VSPHERE_USERNAME": "u",
            "VSPHERE_PASSWORD": "p",
        }
    )

    with pytest.raises(LookupError, match="configured: vc-a"):
        settings.vcenter("vc-z")


# -- verdicts ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("fields", "state"),
    [
        ({"connection_state": "orphaned"}, checks.INACCESSIBLE),
        ({"question": Question("1", "moved or copied?", ["Cancel"])}, checks.BLOCKED_ON_QUESTION),
        ({"power_state": "poweredOff"}, checks.OFF),
        ({"tools_running": "guestToolsRunning", "heartbeat": "green"}, checks.HEALTHY),
        ({"tools_running": "guestToolsRunning", "heartbeat": "gray"}, checks.HEALTHY),
        ({"tools_running": "guestToolsRunning", "heartbeat": "red"}, checks.LOST_HEARTBEAT),
        ({"uptime_minutes": None}, checks.NO_BOOT_TIME),
        ({"uptime_minutes": 4.0}, checks.BOOTING),
        ({"cpu_mhz": 30.0}, checks.HUNG),
        ({"cpu_mhz": 3600.0}, checks.BUSY_NOT_UP),
        ({"cpu_mhz": 900.0}, checks.BOOTED_NOT_UP),
        ({"cpu_mhz": 900.0, "host_core_mhz": None}, checks.BOOTED_NOT_UP),
    ],
)
def test_each_state_is_judged_on_its_own_values(fields: dict[str, object], state: str) -> None:
    verdict = checks.classify(vm(**fields), LIMITS)

    assert verdict.state == state
    assert verdict.values["uptime_minutes"] == fields.get("uptime_minutes", 25.0)


def test_a_question_outranks_everything_but_reachability() -> None:
    verdict = checks.classify(vm(question=Question("1", "q", []), power_state="poweredOff"), LIMITS)

    assert verdict.state == checks.BLOCKED_ON_QUESTION


def test_resets_in_the_window_flag_a_boot_loop() -> None:
    verdict = checks.classify(vm(uptime_minutes=1.0), LIMITS, resets_in_window=3)

    assert verdict.state == checks.BOOTING
    assert verdict.flags == [checks.BOOT_LOOP]
    assert verdict.abnormal


def test_ready_time_is_a_percent_per_vcpu() -> None:
    # 6,000 ms ready in a 20 s sample on 2 vCPUs: 15% each.
    assert checks.ready_percent(6000, 20, 2) == pytest.approx(15.0)


def test_host_usage_is_never_called_overcommitted() -> None:
    by_demand = checks.host_pressure(4000, 4800, None, LIMITS)
    by_usage = checks.host_pressure(4000, None, 4000, LIMITS)

    assert by_demand["overcommitted"] is True
    assert by_demand["percent_of_capacity"] == 120.0
    assert by_usage["overcommitted"] is False
    assert by_usage["near_capacity"] is True


# -- inventory concepts --------------------------------------------------------------


def folder(moref: str, name: str, parent: str | None, path: str, parent_name: str | None) -> FolderFacts:
    return FolderFacts(moref, name, parent, path, parent_name, "DC0")


def test_an_environment_is_found_by_exact_name_before_containing_it() -> None:
    folders = {
        "g1": folder("g1", "env-1001", "p", "/DC0/vm/environments/env-1001", "environments"),
        "g2": folder("g2", "env-10011", "p", "/DC0/vm/environments/env-10011", "environments"),
        "g3": folder("g3", "old-env-1001-copy", "q", "/DC0/vm/archive/old-env-1001-copy", "archive"),
    }

    assert [match.moref for match in find_environment(folders, "ENV-1001")] == ["g1"]
    # Without an exact match, every folder containing the id comes back, for the reader to choose.
    assert {match.moref for match in find_environment(folders, "env-100")} == {"g1", "g2", "g3"}


def test_hinted_parents_come_first_but_nothing_is_dropped() -> None:
    folders = {
        "g1": folder("g1", "env-7", "a", "/DC0/vm/a/b/env-7", "elsewhere"),
        "g2": folder("g2", "env-7", "p", "/DC0/vm/projects/env-7/x/y", "projects"),
    }

    assert [match.moref for match in find_environment(folders, "env-7", ["projects"])] == ["g2", "g1"]
    assert [match.moref for match in find_environment(folders, "env-7")] == ["g1", "g2"]


@pytest.mark.parametrize(
    ("guest_id", "full_name", "family", "expected"),
    [
        ("windows9_64Guest", None, None, "windows"),
        ("winVistaGuest", None, None, "windows"),
        (None, "Microsoft Windows Server 2019", None, "windows"),
        ("otherGuest", None, "windowsGuest", "windows"),
        ("rhel8_64Guest", None, None, "linux"),
        ("otherGuest", None, None, "unknown"),
    ],
)
def test_os_family_from_any_of_three_fields(
    guest_id: str | None, full_name: str | None, family: str | None, expected: str
) -> None:
    assert os_family(guest_id, full_name, family) == expected


# -- vmware.log --------------------------------------------------------------------------

NEW = """\
2026-10-29T02:05:00.100Z In(05) vmx - Transitioned vmx/execState/val to poweredOn
2026-10-29T02:05:02.000Z In(05) vcpu-0 - EFI ROM: boot order: Windows Boot Manager
2026-10-29T02:05:20.000Z In(05) vmx - HBACommon: First write on scsi0:0.fileName='x.vmdk'
2026-10-29T02:06:40.000Z Wa(03) vmx - SCSI0: RESET BUS
  a continuation line
2026-10-29T02:07:00.000Z In(05) vmx - VMXNET3 user: Ethernet0 Driver Info: version = 1
"""
OLD = """\
2016-01-01T00:00:00.000Z| vmx| I125: Transitioned vmx/execState/val to poweredOn
2016-01-01T00:00:30.000Z| vcpu-0| W115: Guest-initiated reset
2016-01-01T00:01:00.000Z| vmx| I125: ToolsSetVersion: Tools version 10346
"""


def test_both_log_formats_parse() -> None:
    new = vmlog.parse_lines(NEW)
    old = vmlog.parse_lines(OLD)

    assert new[3].level == "warning"
    assert new[3].thread == "vmx"
    assert new[4].time is None
    assert old[1].level == "warning"
    assert old[1].message == "Guest-initiated reset"


def test_the_timeline_says_how_far_the_boot_got_and_what_happened() -> None:
    timeline = vmlog.boot_timeline(vmlog.parse_lines(NEW))

    assert timeline["last_stage"] == "guest_drivers"
    assert timeline["not_reached"] == ["tools"]
    assert timeline["annotations"]["storage"]["count"] == 1
    assert timeline["seconds_from_last_stage_to_end_of_log"] == 0


def test_the_timeline_starts_at_the_last_reset() -> None:
    timeline = vmlog.boot_timeline(vmlog.parse_lines(OLD))

    assert timeline["boot_started"] == datetime(2016, 1, 1, 0, 0, 30, tzinfo=UTC)
    assert timeline["last_stage"] == "tools"


def test_a_log_with_no_boot_says_so() -> None:
    timeline = vmlog.boot_timeline(vmlog.parse_lines("2026-10-29T02:05:00.100Z In(05) vmx - nothing here\n"))

    assert timeline["boot_found"] is False


def test_grep_keeps_the_newest_and_counts_all() -> None:
    lines = vmlog.parse_lines(NEW)

    kept, total = vmlog.grep(lines, None, limit=2)
    since, _ = vmlog.grep(lines, ".*", since=datetime(2026, 10, 29, 2, 6, tzinfo=UTC), limit=10)

    assert total == 5
    assert [line.number for line in kept] == [4, 6]
    assert [line.number for line in since] == [4, 5, 6]


def test_stop_codes_by_number_and_by_name() -> None:
    text = "*** STOP: 0x00000101 (0x0, ...)\nlater: Stop code: CRITICAL_PROCESS_DIED\nBugCheck 0x7b"

    codes = vmlog.stop_codes(text)

    assert [code["code"] for code in codes] == ["0x00000101", "0x0000007B", "0x000000EF"]
    assert codes[0]["points_at"].startswith("CPU")
    assert codes[1]["points_at"].startswith("storage")


def test_serial_output_without_ems_or_errors_is_plain() -> None:
    result = vmlog.read_serial("hello\nworld\n", tail_lines=1)

    assert result == {
        "bytes": 12,
        "lines": 2,
        "empty": False,
        "ems_output_seen": False,
        "windows_stop_codes": [],
        "linux_findings": [],
        "tail": ["world"],
    }


# -- the console --------------------------------------------------------------------------


def image(colour: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (200, 150), colour).save(buffer, format="PNG")
    return buffer.getvalue()


def test_black_and_frozen_screens_are_said_in_words() -> None:
    result = console.read_captures(
        [image((0, 0, 0)), image((0, 0, 0))], black_fraction=0.98, frozen_difference=0.5
    )

    assert result["black"] is True
    assert result["frozen"] is True
    assert result["text"] is None
    assert any("not read" in finding for finding in result["findings"])


def test_a_changing_screen_is_not_frozen() -> None:
    result = console.read_captures(
        [image((0, 0, 0)), image((90, 90, 90))], black_fraction=0.98, frozen_difference=0.5
    )

    assert result["frozen"] is False


@pytest.mark.parametrize("colour", [(0, 0, 170), (0, 120, 215)])
def test_both_generations_of_blue_screen_are_recognised(colour: tuple[int, int, int]) -> None:
    assert console.analyse(image(colour))["blue_screen_colour_fraction"] == 1.0


@pytest.mark.parametrize(
    ("text", "state"),
    [
        ("Your PC ran into a problem and needs to restart. Stop code: CRITICAL PROCESS DIED", "blue_screen"),
        ("Working on updates  30% complete. Don't turn off your computer", "windows_updating"),
        ("Preparing Automatic Repair", "automatic_repair"),
        ("Starting Windows", "windows_starting"),
        ("Press Ctrl+Alt+Delete to sign in.", "windows_logon"),
        ("Kernel panic - not syncing: VFS", "linux_panic"),
        ("Getting devices ready 45%", "device_setup"),
    ],
)
def test_ocr_text_names_the_screen(text: str, state: str) -> None:
    assert console.screen_state(text)[0]["state"] == state


# -- grouping a scan ------------------------------------------------------------------------


def scan_of(vms: list[VmFacts]) -> scan.Scan:
    by_vcenter: dict[str, list[VmFacts]] = {}
    for item in vms:
        by_vcenter.setdefault(item.vcenter, []).append(item)
    return scan.Scan(
        id="s1",
        started=NOW,
        vcenters={
            name: scan.VCenterScan(
                inventory=Inventory(name, NOW, members, {}, {}, {}, base_disks_read=True),
                verdicts={item.moref: checks.classify(item, LIMITS) for item in members},
                hosts={},
                storage=None,
            )
            for name, members in by_vcenter.items()
        },
        errors={},
    )


def test_the_strongest_group_is_the_one_that_concentrates_the_stuck_vms() -> None:
    fleet = [
        vm(
            moref=f"vm-{index}",
            host=f"esx-{index % 4}",
            base_disk="[ds] base-a.vmdk" if index < 4 else "[ds] base-b.vmdk",
            datastores=["ds-1"],
            tools_running="guestToolsNotRunning" if index < 3 else "guestToolsRunning",
            heartbeat="green",
        )
        for index in range(20)
    ]

    result = scan.summary(scan_of(fleet), limit=10)

    assert result["strongest_groups"][0]["dimension"] == "base_disk"
    assert result["strongest_groups"][0]["value"] == "vc-a:[ds] base-a.vmdk"
    assert result["strongest_groups"][0]["abnormal"] == 3
    assert result["strongest_groups"][0]["population"] == 4
    # A datastore every VM is on says nothing and is left out.
    assert "datastore" not in result["groups"]


def test_the_same_host_name_on_two_vcenters_is_two_hosts() -> None:
    fleet = [
        vm(vcenter="vc-a", moref="vm-1", host="DC0_H0"),
        vm(vcenter="vc-a", moref="vm-2", host="DC0_H0"),
        vm(vcenter="vc-b", moref="vm-1", host="DC0_H0", tools_running="guestToolsRunning", heartbeat="green"),
        vm(vcenter="vc-b", moref="vm-2", host="DC0_H0", tools_running="guestToolsRunning", heartbeat="green"),
    ]

    hosts = {row["value"]: row for row in scan.groups(scan_of(fleet))["host"]}

    assert hosts["vc-a:DC0_H0"]["population"] == 2
    assert "vc-b:DC0_H0" not in hosts


def test_representatives_span_the_boot_times() -> None:
    members = [vm(moref=f"vm-{index}", boot_time=NOW - timedelta(minutes=index)) for index in range(7)]

    picked = scan.representatives(members)

    assert [item.moref for item in picked] == ["vm-6", "vm-3", "vm-0"]


# -- conclusions ------------------------------------------------------------------------------


def conclude(**parts: dict) -> dict:
    defaults: dict[str, dict] = {
        "cpu": {"findings": [], "starved": False},
        "disk": {"findings": [], "slow": False, "datastores": []},
        "environment": {"signals": []},
        "logs": {"available": False},
        "serial": {"available": False},
        "console": {"available": False},
        "host_log": {"available": False},
    }
    defaults.update(parts)
    machine = vm(cpu_mhz=3600.0)
    return diagnose.conclude(checks.classify(machine, LIMITS), **defaults)


def test_cpu_evidence_from_three_places_is_high_confidence() -> None:
    result = conclude(
        cpu={"findings": ["ready 30%", "host at 120%"], "starved": True},
        environment={"signals": [{"kind": "only_abnormal_on", "dimension": "host", "values": ["esx-1"]}]},
    )

    assert result["causes"][0]["cause"] == diagnose.CPU
    assert result["causes"][0]["confidence"] == "high"
    assert "booting slowly" in result["headline"]


def test_healthy_neighbours_on_the_same_datastore_argue_against_it() -> None:
    result = conclude(
        disk={"findings": ["datastore ds-1 write latency peaked at 60 ms"], "slow": True, "datastores": []},
        environment={
            "signals": [{"kind": "shared_with_healthy", "dimension": "datastore", "values": ["ds-1"]}]
        },
    )

    storage = next(cause for cause in result["causes"] if cause["cause"] == diagnose.STORAGE)
    assert storage["against"] == ["healthy VMs in its environment are on the same datastore ds-1"]
    assert storage["confidence"] != "high"


def test_a_stop_code_on_the_serial_console_names_the_crash_and_its_layer() -> None:
    serial = {
        "available": True,
        "files": [
            {
                "windows_stop_codes": [
                    {
                        "code": "0x0000007A",
                        "name": "KERNEL_DATA_INPAGE_ERROR",
                        "points_at": "storage: paging I/O failed",
                    }
                ],
                "linux_findings": [],
            }
        ],
    }

    result = conclude(serial=serial)

    assert [cause["cause"] for cause in result["causes"]][:2] == [diagnose.WINDOWS_CRASH, diagnose.STORAGE]


def test_nothing_read_is_listed_as_not_checked() -> None:
    result = conclude(cpu={"available": False, "reason": "x"})

    assert "CPU counters" in result["not_checked"]
    assert "console screen" in result["not_checked"]


def test_the_check_window_starts_before_the_boot() -> None:
    boot = NOW - timedelta(minutes=20)

    assert diagnose.window(NOW, boot) == (boot - timedelta(minutes=2), NOW)
    old = NOW - timedelta(hours=5)
    assert diagnose.window(NOW, old) == (old - timedelta(minutes=5), old + timedelta(minutes=30))


# -- counters ---------------------------------------------------------------------------------


def test_datastore_instances_try_the_volume_id_then_the_name() -> None:
    assert contention.datastore_instances({"url": "ds:///vmfs/volumes/5f1a-22/", "name": "pflex-07"}) == [
        "5f1a-22",
        "pflex-07",
    ]
    assert contention.datastore_instances({"url": "/sim/x/DC0-LocalDS_0", "name": "LocalDS_0"}) == [
        "LocalDS_0",
        "DC0-LocalDS_0",
    ]


def test_a_series_is_summarised_with_its_peak() -> None:
    samples = [(NOW + timedelta(seconds=20 * index), value) for index, value in enumerate([1.0, 9.0, 4.0])]

    summary = contention.summarize(samples)

    assert summary is not None
    assert (summary["max"], summary["mean"], summary["last"]) == (9.0, 4.67, 4.0)
    assert summary["peak_at"] == NOW + timedelta(seconds=20)


# -- read-only --------------------------------------------------------------------------------


class Inner:
    version = "vim.version.v8_0_2_0"
    cookie = 'vmware_soap_session="abc"; Path=/'

    def __init__(self) -> None:
        self.sent: list[str] = []

    def InvokeMethod(self, _mo: object, info: object, _args: object, _outer: object) -> tuple[int, str]:  # noqa: N802
        self.sent.append(info.wsdlName)  # type: ignore[attr-defined]
        return 200, "ok"


class Info:
    def __init__(self, name: str) -> None:
        self.wsdlName = name


def test_a_write_is_refused_before_anything_is_sent() -> None:
    inner = Inner()
    stub = ReadOnlyStub(inner)

    for name in (
        "PowerOffVM_Task",
        "AnswerVM",
        "CreateScreenshot_Task",
        "ReconfigVM_Task",
        "Destroy_Task",
        "CreateFolder",
    ):
        with pytest.raises(ReadOnlyViolationError):
            stub.InvokeMethod(None, Info(name), ())
    assert stub.InvokeMethod(None, Info("RetrievePropertiesEx"), ()) == "ok"
    assert inner.sent == ["RetrievePropertiesEx"]
    assert stub.seen == {"RetrievePropertiesEx"}


def test_nothing_on_the_read_list_writes() -> None:
    writes = (
        "Power",
        "Reset",
        "Reboot",
        "Shutdown",
        "Answer",
        "Reconfig",
        "Create",
        "Destroy",
        "Delete",
        "Move",
        "Relocate",
        "Migrate",
        "Clone",
        "Register",
        "Upload",
        "Rename",
        "Remove",
        "Mount",
        "Revert",
        "Snapshot",
        "Consolidate",
        "Screenshot",
        "Put",
        "Update",
    )
    # Session-scoped views and collectors: created and destroyed within this session, changing nothing.
    allowed_sessions = {"CreateContainerView", "DestroyView"}

    for name in ALLOWED_METHODS - allowed_sessions:
        assert not any(word in name for word in writes), name


@pytest.mark.parametrize("method", ["PUT", "POST", "DELETE", "PATCH"])
def test_http_writes_are_refused(method: str) -> None:
    with pytest.raises(ReadOnlyViolationError):
        ensure_read_request(method)
    ensure_read_request("get")


# -- results ------------------------------------------------------------------------------------


def test_results_are_json_with_utc_times_and_no_private_keys() -> None:
    result = formatting.bounded({"when": datetime(2026, 1, 1, 3, tzinfo=UTC), "_ref": object(), "n": 1.23456})

    assert result == {"when": "2026-01-01T03:00:00Z", "n": 1.235}


def test_a_large_result_is_cut_and_says_so() -> None:
    result = formatting.bounded({"findings": ["a"], "rows": [{"text": "x" * 500} for _ in range(2000)]})

    assert "truncated" in result
    assert len(json.dumps(result)) <= formatting.MAX_RESPONSE_CHARACTERS
    assert result["findings"] == ["a"]


# -- vROps ----------------------------------------------------------------------------------------


def test_vrops_logs_in_once_and_compares_a_window_with_previous_days() -> None:
    requests: list[httpx.Request] = []
    begin = datetime(2026, 10, 29, 2, 0, tzinfo=UTC)

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/auth/token/acquire"):
            return httpx.Response(200, json={"token": "t-1"})
        if request.url.path.endswith("/stats"):
            start = int(request.url.params["begin"])
            days_ago = round((begin.timestamp() * 1000 - start) / 86_400_000)
            peak = 135.0 if days_ago == 0 else 90.0 + days_ago
            return httpx.Response(
                200,
                json={
                    "values": [
                        {
                            "stat-list": {
                                "stat": [
                                    {
                                        "statKey": {"key": "cpu|demandPct"},
                                        "timestamps": [start, start + 300_000],
                                        "data": [50.0, peak],
                                    }
                                ]
                            }
                        }
                    ]
                },
            )
        return httpx.Response(404)

    settings = Settings.from_environment(
        {
            "VSPHERE_VROPS_URL": "https://vrops.example/",
            "VSPHERE_VROPS_USERNAME": "reader",
            "VSPHERE_VROPS_PASSWORD": "secret",
        }
    )
    client = Vrops(settings, transport=httpx.MockTransport(respond))

    result = asyncio.run(
        client.compare(
            "host-1",
            ["cpu|demandPct"],
            begin,
            begin + timedelta(minutes=30),
            baseline_days=3,
            interval_minutes=5,
        )
    )

    assert result["cpu|demandPct"]["window_max"] == 135.0
    assert result["cpu|demandPct"]["unusual"] is True
    assert result["cpu|demandPct"]["baseline_max_of_maxes"] == 93.0
    assert sum(1 for request in requests if request.url.path.endswith("acquire")) == 1
    assert all(
        request.headers["Authorization"] == "vRealizeOpsToken t-1"
        for request in requests
        if request.method == "GET"
    )


# -- the signals beyond "stuck" ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("fields", "state"),
    [
        ({"paused": True}, checks.PAUSED),
        ({"power_state": "suspended"}, checks.SUSPENDED),
        ({"tools_status": "toolsNotInstalled", "cpu_mhz": 3000.0}, checks.NO_TOOLS),
        ({"tools_status": "toolsNotRunning"}, checks.HUNG),
        ({"tools_running": "guestToolsExecutingScripts", "cpu_mhz": 900.0}, checks.BOOTED_NOT_UP),
    ],
)
def test_the_newer_states(fields: dict[str, object], state: str) -> None:
    assert checks.classify(vm(**fields), LIMITS).state == state


def test_a_vm_without_tools_is_not_abnormal_but_is_explained() -> None:
    verdict = checks.classify(vm(tools_status="toolsNotInstalled", cpu_mhz=2000.0), LIMITS)

    assert not verdict.abnormal
    assert "toolsNotInstalled" in verdict.reasons[0]
    assert "50%" in verdict.reasons[0]


@pytest.mark.parametrize(
    ("fields", "flag", "attention"),
    [
        ({"tools_running": "guestToolsRunning", "heartbeat": "yellow"}, checks.HEARTBEAT_INTERMITTENT, True),
        ({"swapped_mb": 10}, checks.MEMORY_RECLAIMED, True),
        ({"ballooned_mb": 10}, checks.MEMORY_RECLAIMED, True),
        ({"host_memory_percent": 97.0}, checks.HOST_MEMORY_PRESSURE, True),
        ({"alarms": [{"alarm": "VM CPU", "status": "red"}]}, checks.VCENTER_ALARM, True),
        ({"host_connection_state": "notResponding"}, checks.HOST_NOT_CONNECTED, True),
        ({"created": NOW - timedelta(hours=30), "read_at": NOW}, checks.LONG_RUNNING, True),
        ({"host_maintenance": True}, checks.HOST_IN_MAINTENANCE, False),
        ({"tools_version_status": "guestToolsTooOld"}, checks.TOOLS_OUTDATED, False),
    ],
)
def test_each_flag_and_whether_it_matters_alone(
    fields: dict[str, object], flag: str, attention: bool
) -> None:
    healthy = {"tools_running": "guestToolsRunning", "heartbeat": "green"}

    verdict = checks.classify(vm(**(healthy | fields)), LIMITS)

    assert flag in verdict.flags
    assert verdict.abnormal is attention
    assert verdict.as_dict()["flags_meaning"][flag]


def test_a_yellow_alarm_alone_is_not_flagged() -> None:
    verdict = checks.classify(vm(alarms=[{"alarm": "x", "status": "yellow"}]), LIMITS)

    assert checks.VCENTER_ALARM not in verdict.flags


def test_age_is_measured_by_vcenters_clock_and_unknown_without_a_create_date() -> None:
    assert vm(created=NOW - timedelta(hours=6), read_at=NOW).age_hours == pytest.approx(6.0)
    assert vm(created=None, read_at=NOW).age_hours is None


@pytest.mark.parametrize(
    ("path", "terms", "inside"),
    [
        ("/DC0/vm/projects/env-1", ["projects"], True),
        ("/DC0/vm/projects/team-x/env-1", ["projects/"], True),
        ("/DC0/vm/projects/team-x/env-1", ["/projects/team-x/"], True),
        ("/DC0/vm/projects/team-y/env-1", ["projects/team-x"], False),
        ("/DC0/vm/environments/env-1", ["Environments"], True),
        ("/DC0/vm/my-projects-old/env-1", ["projects"], False),
        ("/DC0/vm/env-1", [], True),
        (None, ["projects"], False),
    ],
)
def test_under_matches_whole_segments(path: str | None, terms: list[str], inside: bool) -> None:
    assert ages.under_any(path, terms) is inside


def test_a_property_vcenter_rejects_is_dropped_not_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings.from_environment(
        {
            "VSPHERE_VCENTERS": '[{"name": "vc-a", "host": "a"}]',
            "VSPHERE_USERNAME": "u",
            "VSPHERE_PASSWORD": "p",
        }
    )
    session = VCenterSession(settings.vcenters[0], settings)
    asked: list[list[str]] = []

    def once(_kind: object, paths: list[str], *, root: object, objects: object) -> list[dict]:
        asked.append(list(paths))
        if "runtime.paused" in paths:
            raise vmodl.query.InvalidProperty(name="runtime.paused")
        return [{"moref": "vm-1", "name": "x"}]

    monkeypatch.setattr(session, "_retrieve_once", once)

    rows = session.retrieve(object, ["name", "runtime.paused"])

    assert asked == [["name", "runtime.paused"], ["name"]]
    assert rows == [{"moref": "vm-1", "name": "x", "_missing": ["runtime.paused"]}]


# -- reboot time (a warm reboot does not move runtime.bootTime) --------------------------------


def test_a_power_on_days_ago_with_a_recent_reboot_event_is_booting_not_hung() -> None:
    from vsphere_mcp.inventory import set_effective_boot

    machine = vm(
        moref="vm-7",
        power_on_time=NOW - timedelta(days=3),
        boot_time=NOW - timedelta(days=3),
        uptime_minutes=3 * 24 * 60,
        read_at=NOW,
        tools_running="guestToolsNotRunning",
        cpu_mhz=1500.0,
    )
    # Without the reboot event: looks stuck for days.
    assert checks.classify(machine, LIMITS).state in (checks.HUNG, checks.BUSY_NOT_UP, checks.BOOTED_NOT_UP)

    set_effective_boot(machine, NOW, reboots={"vm-7": NOW - timedelta(minutes=3)})

    assert machine.boot_source == "reboot_event"
    assert machine.uptime_minutes == pytest.approx(3.0)
    assert checks.classify(machine, LIMITS).state == checks.BOOTING


def test_a_reported_reboot_time_wins_over_an_older_event() -> None:
    from vsphere_mcp.inventory import set_effective_boot

    machine = vm(moref="vm-7", power_on_time=NOW - timedelta(days=1), read_at=NOW)

    set_effective_boot(
        machine,
        NOW,
        reboots={"vm-7": NOW - timedelta(hours=2)},
        rebooted_at=NOW - timedelta(minutes=12),
    )

    assert machine.boot_source == "reported_reboot"
    assert machine.uptime_minutes == pytest.approx(12.0)


def test_uptime_from_power_on_with_tools_down_carries_a_caution() -> None:
    from vsphere_mcp.inventory import set_effective_boot

    machine = vm(
        moref="vm-7",
        power_on_time=NOW - timedelta(hours=5),
        read_at=NOW,
        tools_running="guestToolsNotRunning",
    )

    set_effective_boot(machine, NOW, reboots={})

    assert machine.boot_source == "power_on"
    assert any("in-guest reboot" in note for note in machine.notes)


def test_latest_reboot_picks_the_most_recent_event_per_vm() -> None:
    def event(moref: str, when: datetime, kind: str) -> object:
        vm_arg = type("M", (), {"_moId": moref})()
        # The class name is what the code reads, so give each the real event type name.
        return type(kind, (), {"vm": type("A", (), {"vm": vm_arg})(), "createdTime": when})()

    events = [
        event("vm-1", NOW - timedelta(minutes=30), "VmResettingEvent"),
        event("vm-1", NOW - timedelta(minutes=5), "VmResettingEvent"),
        event("vm-2", NOW - timedelta(minutes=10), "VmGuestRebootEvent"),
        event("vm-3", NOW, "VmPoweredOnEvent"),  # not a reboot
    ]

    latest = checks.latest_reboot_by_vm(events)

    assert latest["vm-1"] == NOW - timedelta(minutes=5)
    assert latest["vm-2"] == NOW - timedelta(minutes=10)
    assert "vm-3" not in latest
