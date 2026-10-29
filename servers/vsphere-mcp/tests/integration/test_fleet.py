"""The server against two simulated vCenters: every incident kind, and the read-only proof."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from conftest import call, png
from pyVmomi import vim

from vsphere_mcp.readonly import ALLOWED_METHODS, ReadOnlyViolationError, ensure_read_request
from vsphere_mcp.vcenter import VCenterSession

if TYPE_CHECKING:
    import scenario
    from mcp.server import MCPServer


def states(result: dict[str, Any]) -> dict[str, str]:
    return {f"{vm['folder']}/{vm['name']}": vm["verdict"]["state"] for vm in result["abnormal_vms"]}


def causes(result: dict[str, Any]) -> list[str]:
    return [cause["cause"] for cause in result["conclusion"]["causes"]]


# -- the fleet ------------------------------------------------------------------------


def test_both_vcenters_are_reached(server: MCPServer) -> None:
    result = call(server, "list_vcenters")

    assert [row["name"] for row in result["vcenters"]] == ["vc-a", "vc-b"]
    assert all(row["reachable"] for row in result["vcenters"])
    assert result["vrops_configured"] is False


def test_scan_judges_each_kind_of_stuck_vm(server: MCPServer) -> None:
    result = call(server, "scan", {"limit": 100})

    found = states(result)
    assert found["env-1001/web-01"] == "hung"
    assert found["env-1001/db-01"] == "hung"
    assert found["env-1002/web-01"] == "busy_not_up"
    assert found["env-1003/asks-01"] == "blocked_on_question"
    assert found["env-1003/bsod-01"] == "hung"
    assert found["env-1003/lnx-01"] == "busy_not_up"
    # Booted a minute ago, so not stuck; reset four times, so flagged.
    assert found["env-1003/loop-01"] == "booting"
    loop = next(vm for vm in result["abnormal_vms"] if vm["name"] == "loop-01")
    assert "boot_loop" in loop["verdict"]["flags"]
    # Healthy, booting and powered-off VMs are not listed as abnormal.
    assert "env-1003/fresh-01" not in found
    assert "env-1003/ok-01" not in found
    assert "env-1003/off-01" not in found
    assert result["counts_by_state"]["healthy"] >= 7


def test_scan_leads_with_what_the_stuck_vms_share(server: MCPServer) -> None:
    result = call(server, "scan")

    strongest = [(row["dimension"], row["value"]) for row in result["strongest_groups"]]
    assert ("base_disk", "vc-a:[LocalDS_0] base-win10/base-win10.vmdk") in strongest[:3]
    assert ("host", "vc-a:DC0_C1_H0") in strongest
    over = [(host["vcenter"], host["name"]) for host in result["hosts_over_cpu_threshold"]]
    assert over == [("vc-a", "DC0_C1_H0")]
    assert any("LocalDS_0" in finding and "latency" in finding for finding in result["storage_findings"])


def test_scan_keeps_same_named_hosts_on_different_vcenters_apart(server: MCPServer) -> None:
    result = call(server, "scan")

    values = [row["value"] for row in result["groups"].get("host", [])]
    assert all(value.startswith(("vc-a:", "vc-b:")) for value in values)
    assert "vc-b:DC0_C0_H0" not in values  # every VM there is healthy


def test_scan_can_ask_for_one_state(server: MCPServer) -> None:
    result = call(server, "scan", {"states": ["blocked_on_question"], "vcenters": ["vca.lab.example"]})

    assert [vm["name"] for vm in result["abnormal_vms"]] == ["asks-01"]
    assert list(result["vcenters"]) == ["vc-a"]


def test_explain_group_names_the_slow_datastore_behind_a_base_disk(server: MCPServer) -> None:
    scan = call(server, "scan")

    result = call(
        server,
        "explain_group",
        {
            "scan_id": scan["scan_id"],
            "dimension": "base_disk",
            "value": "vc-a:[LocalDS_0] base-win10/base-win10.vmdk",
        },
    )

    assert result["found"] is True
    assert result["states"] == {"hung": 3}
    assert any("LocalDS_0" in finding and "180 ms" in finding for finding in result["findings"])
    assert {vm["name"] for vm in result["representatives"]} == {"web-01", "db-01", "app-01"}


def test_explain_group_says_which_hosts_are_overcommitted(server: MCPServer) -> None:
    scan = call(server, "scan")

    result = call(
        server, "explain_group", {"scan_id": scan["scan_id"], "dimension": "host", "value": "vc-a:DC0_C1_H0"}
    )

    assert any("DC0_C1_H0" in finding and "120" in finding for finding in result["findings"])


def test_an_unknown_scan_is_answered_not_raised(server: MCPServer) -> None:
    result = call(server, "explain_group", {"scan_id": "nope", "dimension": "host", "value": "x"})

    assert result["found"] is False
    assert "run scan again" in result["reason"]


# -- one VM: the incidents -------------------------------------------------------------


def test_storage_storm_on_a_shared_base_disk(server: MCPServer, worlds: tuple[scenario.World, ...]) -> None:
    # As a Sahara Tools error names it: the vCenter by an alias, the env id, the machine.
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "VCA.lab.example", "env_id": "env-1001", "vm_name": "web-01", "console_captures": 0},
    )

    assert result["vm"]["moref"] == worlds[0].moref("environments/env-1001", "web-01")
    assert result["vm"]["os_family"] == "windows"
    assert causes(result)[0] == "storage latency (datastore / PowerFlex)"
    assert result["machine"]["state"] == "hung"
    assert result["storage"]["datastores"][0]["matched_instance"] == "LocalDS_0"
    timeline = result["boot"]["timeline"]
    assert timeline["last_stage"] == "firmware"
    assert "guest_drivers" in timeline["not_reached"]
    assert result["boot"]["previous_log"]["available"] is True
    assert [item["name"] for item in result["boot"]["log_files"]] == ["vmware.log", "vmware-1.log"]
    assert result["environment"]["counts_by_state"] == {"hung": 3, "healthy": 1}
    assert any(signal["dimension"] == "datastore" for signal in result["environment"]["signals"])
    assert "console screen" in result["conclusion"]["not_checked"]


def test_cpu_starvation_on_an_overcommitted_host(
    server: MCPServer, worlds: tuple[scenario.World, ...]
) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1002", "vm_name": "web-01", "console_captures": 0},
    )

    # Same name as env-1001's web-01; a different machine.
    assert result["vm"]["moref"] == worlds[0].moref("environments/env-1002", "web-01")
    assert causes(result)[0] == "CPU starvation (ESXi overcommit)"
    assert result["machine"]["state"] == "busy_not_up"
    assert "booting slowly" in result["finding"]
    assert result["cpu"]["vm_ready_percent_per_vcpu"]["max"] == pytest.approx(30.0)
    assert result["cpu"]["host"]["overcommitted"] is True
    # The ESXi 6 log format is read as well as the 7+ one.
    assert result["boot"]["timeline"]["last_stage"] == "guest_drivers"


def test_a_pending_question_is_the_cause_when_there_is_one(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1003", "vm_name": "asks-01", "console_captures": 0},
    )

    assert causes(result)[0] == "a pending VM question blocks it"
    assert result["conclusion"]["causes"][0]["confidence"] == "high"
    assert result["machine"]["question"]["choices"] == ["Cancel", "I Moved It", "I Copied It"]


def test_ems_on_the_serial_port_gives_the_stop_code(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1003", "vm_name": "bsod-01", "console_captures": 0},
    )

    serial = result["serial_console"]["files"][0]
    assert serial["ems_output_seen"] is True
    assert serial["windows_stop_codes"] == [
        {
            "code": "0x0000007A",
            "name": "KERNEL_DATA_INPAGE_ERROR",
            "points_at": "storage: paging I/O failed or timed out",
        }
    ]
    assert causes(result)[0] == "Windows crashed (stop error)"
    assert result["vm"]["guest_os"] == "Microsoft Windows 7 (64-bit)"


def test_no_serial_port_is_normal_and_said(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1001", "vm_name": "db-01", "console_captures": 0},
    )

    assert result["serial_console"]["available"] is False
    assert "no serial port" in result["serial_console"]["reason"]
    assert result["boot"]["previous_log"]["available"] is False


def test_an_empty_serial_file_has_no_findings(server: MCPServer, worlds: tuple[scenario.World, ...]) -> None:
    moref = worlds[0].moref("environments/env-1003", "ok-01")

    result = call(server, "read_serial_console", {"vcenter": "vc-a", "moref": moref})

    assert result["files"][0]["empty"] is True
    assert result["files"][0]["windows_stop_codes"] == []


def test_a_linux_kernel_console_is_read_too(server: MCPServer, worlds: tuple[scenario.World, ...]) -> None:
    moref = worlds[0].moref("environments/env-1003", "lnx-01")

    result = call(server, "read_serial_console", {"vcenter": "vc-a", "moref": moref})

    kinds = {finding["kind"]: finding["points_at"] for finding in result["files"][0]["linux_findings"]}
    assert kinds["soft_lockup"].startswith("CPU")
    assert "hung_task" in kinds
    assert result["vm"]["os_family"] == "linux"


def test_a_boot_loop_is_flagged_from_events(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1003", "vm_name": "loop-01", "console_captures": 0},
    )

    assert "boot_loop" in result["machine"]["flags"]
    assert sum(1 for event in result["events"] if event["type"] == "VmResettingEvent") == 4


def test_a_black_frozen_console_counts_as_an_early_hang(
    server: MCPServer, worlds: tuple[scenario.World, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    # vcsim has no /screen endpoint; vCenter's answer is stood in for.
    monkeypatch.setattr(
        VCenterSession, "screenshot", lambda _self, _moref: (200, png((0, 0, 0)), "image/png")
    )

    result = call(
        server,
        "diagnose_vm",
        {
            "vcenter": "vc-a",
            "env_id": "env-1001",
            "vm_name": "web-01",
            "console_captures": 2,
            "console_interval_seconds": 1,
        },
    )

    console = result["console"]
    assert console["black"] is True
    assert console["frozen"] is True
    hang = next(
        cause for cause in result["conclusion"]["causes"] if cause["cause"] == "the guest hung early in boot"
    )
    assert "console black and unchanged across captures" in hang["for"]


def test_a_blue_console_is_read_as_a_stop_error(
    server: MCPServer, worlds: tuple[scenario.World, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        VCenterSession, "screenshot", lambda _self, _moref: (200, png((0, 120, 215)), "image/png")
    )
    moref = worlds[0].moref("environments/env-1003", "bsod-01")

    result = call(
        server, "get_vm_console", {"vcenter": "vc-a", "moref": moref, "captures": 1, "include_image": True}
    )

    assert any("blue-screen blue" in finding for finding in result["findings"])
    assert result["image_jpeg_base64"]


def test_the_simulators_missing_console_is_reported_not_raised(
    server: MCPServer, worlds: tuple[scenario.World, ...]
) -> None:
    moref = worlds[0].moref("environments/env-1001", "web-01")

    result = call(server, "get_vm_console", {"vcenter": "vc-a", "moref": moref, "captures": 1})

    assert result["available"] is False
    assert "HTTP 404" in result["reason"]


# -- finding things, and not finding them ---------------------------------------------


def test_an_environment_on_two_vcenters_is_found_on_both(server: MCPServer) -> None:
    result = call(server, "find_environment", {"env_id": "env-1001"})

    assert sorted((match["vcenter"], match["parent"]) for match in result["matches"]) == [
        ("vc-a", "environments"),
        ("vc-b", "projects"),
    ]
    assert "2 folders match" in result["finding"]


def test_an_environment_is_found_by_its_exact_name_first(server: MCPServer) -> None:
    result = call(server, "find_environment", {"env_id": "env-2001", "vcenter": "vc-b"})

    exact = [match for match in result["matches"] if match["exact"]]
    assert [match["folder"] for match in exact] == ["/DC0/vm/projects/env-2001"]
    assert result["finding"].startswith("found at /DC0/vm/projects/env-2001")


def test_a_partial_env_id_is_ambiguous_and_said_so(server: MCPServer) -> None:
    result = call(server, "find_environment", {"env_id": "env-200", "vcenter": "vc-b"})

    assert sorted(match["folder"] for match in result["matches"]) == [
        "/DC0/vm/projects/env-2001",
        "/DC0/vm/projects/env-20015",
    ]
    assert "2 folders match" in result["finding"]


def test_a_name_is_never_looked_up_outside_its_environment(server: MCPServer) -> None:
    result = call(server, "diagnose_vm", {"vcenter": "vc-a", "env_id": "env-1003", "vm_name": "web-01"})

    assert result["found"] is False
    assert "no VM named 'web-01'" in result["reason"]
    assert "asks-01" in result["vms_in_environment"]


def test_a_destroyed_vm_is_reported_as_such(server: MCPServer) -> None:
    result = call(server, "diagnose_vm", {"vcenter": "vc-a", "moref": "vm-99999"})

    assert result["found"] is False
    assert "destroyed" in result["reason"]


def test_an_unknown_vcenter_names_the_configured_ones(server: MCPServer) -> None:
    result = call(server, "diagnose_vm", {"vcenter": "vc-zz", "moref": "vm-1"})

    assert result["found"] is False
    assert "vc-a, vc-b" in result["reason"]


def test_an_environment_is_diagnosed_as_a_whole(server: MCPServer) -> None:
    result = call(server, "diagnose_environment", {"vcenter": "vc-a", "env_id": "env-1001"})

    assert result["folder"] == "/DC0/vm/environments/env-1001"
    assert result["counts_by_state"] == {"hung": 3, "healthy": 1}
    assert any("LocalDS_0" in finding for finding in result["findings"])
    assert result["pattern"]["abnormal_base_disks"] == {"[LocalDS_0] base-win10/base-win10.vmdk": 3}


# -- the pieces ---------------------------------------------------------------------------


def test_read_vm_log_filters_on_the_server(server: MCPServer, worlds: tuple[scenario.World, ...]) -> None:
    moref = worlds[0].moref("environments/env-1001", "web-01")

    relevant = call(server, "read_vm_log", {"vcenter": "vc-a", "moref": moref})
    everything = call(server, "read_vm_log", {"vcenter": "vc-a", "moref": moref, "all_lines": True})
    previous = call(
        server, "read_vm_log", {"vcenter": "vc-a", "moref": moref, "which": 1, "pattern": "tools"}
    )

    assert relevant["matched"] == 4
    assert everything["returned"] == 4
    assert [line["message"] for line in previous["lines"]] == [
        "ToolsSetVersion: Tools version 12352 (current)"
    ]


def test_get_boot_timeline(server: MCPServer, worlds: tuple[scenario.World, ...]) -> None:
    moref = worlds[0].moref("environments/env-1003", "bsod-01")

    result = call(server, "get_boot_timeline", {"vcenter": "vc-a", "moref": moref})

    assert [stage["stage"] for stage in result["boot"]["timeline"]["stages"]] == [
        "power_on_or_reset",
        "firmware",
        "guest_disk_io",
        "guest_drivers",
    ]
    assert result["serial_console"]["available"] is True


def test_get_vm_events_works_by_moref(server: MCPServer, worlds: tuple[scenario.World, ...]) -> None:
    moref = worlds[0].moref("environments/env-1003", "loop-01")

    result = call(server, "get_vm_events", {"vcenter": "vc-a", "moref": moref})

    assert [event["type"] for event in result["events"]].count("VmResettingEvent") == 4


def test_host_health(server: MCPServer) -> None:
    result = call(server, "get_host_health", {"vcenter": "vc-a", "host": "dc0_c1_h0"})

    assert result["cpu"]["overcommitted"] is True
    assert result["cpu"]["peak_percent_of_capacity"] == pytest.approx(120.0)
    assert {vm["name"] for vm in result["abnormal_vms"]} == {"web-01", "db-01"}


def test_datastore_health(server: MCPServer) -> None:
    result = call(server, "get_datastore_health", {"vcenter": "vc-a", "datastore": "LocalDS_0"})

    assert result["storage"]["slow"] is True
    assert result["vms"] >= 3
    assert {vm["name"] for vm in result["abnormal_vms"]} >= {"web-01", "db-01", "app-01"}


def test_a_host_log_the_simulator_lacks_is_reported(server: MCPServer) -> None:
    result = call(server, "read_host_log", {"vcenter": "vc-a", "host": "DC0_C0_H0"})

    assert result["available"] is False
    assert "BrowseDiagnosticLog" in result["reason"]


def test_a_past_window_counts_resets_by_host(server: MCPServer) -> None:
    result = call(server, "diagnose_window", {"vcenters": ["vc-a"], "minutes": 30})

    assert result["vcenters"]["vc-a"]["events_by_host"]["DC0_C1_H2"] == 4
    assert any("4 resets" in finding for finding in result["findings"])


# -- read-only, proven ----------------------------------------------------------------------


def test_every_call_the_tools_made_is_on_the_read_list(
    server: MCPServer, worlds: tuple[scenario.World, ...]
) -> None:
    a = worlds[0]
    scan = call(server, "scan")
    call(
        server, "explain_group", {"scan_id": scan["scan_id"], "dimension": "host", "value": "vc-a:DC0_C1_H0"}
    )
    call(server, "find_environment", {"env_id": "env-1001"})
    for env, name in (("env-1001", "web-01"), ("env-1003", "bsod-01"), ("env-1003", "loop-01")):
        call(
            server, "diagnose_vm", {"vcenter": "vc-a", "env_id": env, "vm_name": name, "console_captures": 1}
        )
    call(server, "diagnose_environment", {"vcenter": "vc-a", "env_id": "env-1002"})
    moref = a.moref("environments/env-1003", "lnx-01")
    for tool in (
        "get_boot_timeline",
        "read_vm_log",
        "read_serial_console",
        "get_vm_console",
        "get_vm_events",
    ):
        call(server, tool, {"vcenter": "vc-a", "moref": moref})
    call(server, "get_host_health", {"vcenter": "vc-a", "host": "DC0_C0_H0"})
    call(server, "get_datastore_health", {"vcenter": "vc-a", "datastore": "LocalDS_1"})
    call(server, "read_host_log", {"vcenter": "vc-a", "host": "DC0_C0_H0"})
    call(server, "diagnose_window", {"minutes": 10})

    seen = server.vcenters.methods_seen()
    assert seen
    assert seen <= ALLOWED_METHODS, seen - ALLOWED_METHODS


def test_a_write_cannot_be_sent_even_from_inside(
    server: MCPServer, worlds: tuple[scenario.World, ...]
) -> None:
    call(server, "list_vcenters")
    session = server.vcenters.session("vc-a")
    vm = session.reference("VirtualMachine", worlds[0].moref("environments/env-1003", "asks-01"))

    for attempt in (
        vm.PowerOffVM_Task,
        vm.ResetVM_Task,
        lambda: vm.AnswerVM("question-1", "2"),
        lambda: vm.ReconfigVM_Task(vim.vm.ConfigSpec(numCPUs=8)),
        vm.Destroy_Task,
        vm.CreateScreenshot_Task,
    ):
        with pytest.raises(ReadOnlyViolationError):
            attempt()
    with pytest.raises(ReadOnlyViolationError):
        ensure_read_request("PUT")
    # And the VM is as it was.
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1003", "vm_name": "asks-01", "console_captures": 0},
    )
    assert result["machine"]["state"] == "blocked_on_question"
