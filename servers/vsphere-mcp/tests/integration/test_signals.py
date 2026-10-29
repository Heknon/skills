"""The signals beyond "stuck", and finding environments that have lived too long."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import pytest
from conftest import call
from mcp.server.mcpserver.exceptions import ToolError, UnexpectedToolError

from vsphere_mcp.config import Settings, VCenter
from vsphere_mcp.server import build_server

if TYPE_CHECKING:
    from mcp.server import MCPServer


def by_name(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {vm["name"]: vm["verdict"] for vm in result["abnormal_vms"] if vm["folder"] == "env-1004"}


# -- states and flags -------------------------------------------------------------------


def test_a_vm_without_tools_is_not_called_stuck(server: MCPServer) -> None:
    everything = call(server, "scan", {"vcenters": ["vc-a"], "limit": 200})
    only = call(server, "scan", {"vcenters": ["vc-a"], "states": ["no_tools"]})

    assert "notools-01" not in by_name(everything)
    assert [vm["name"] for vm in only["abnormal_vms"]] == ["notools-01"]
    assert only["abnormal_vms"][0]["verdict"]["values"]["tools_status"] == "toolsNotInstalled"
    assert everything["counts_by_state"]["no_tools"] == 1


def test_paused_and_suspended_are_their_own_states(server: MCPServer) -> None:
    result = call(server, "scan", {"vcenters": ["vc-a"], "limit": 200})

    assert by_name(result)["paused-01"]["state"] == "paused"
    assert "susp-01" not in by_name(result)
    assert result["counts_by_state"]["suspended"] == 1


def test_tools_stuck_running_its_startup_scripts_is_said_so(server: MCPServer) -> None:
    result = call(server, "scan", {"vcenters": ["vc-a"], "limit": 200})

    starting = by_name(result)["starting-01"]
    assert starting["state"] == "booted_not_up"
    assert "startup scripts" in starting["reasons"][0]


def test_flags_mark_healthy_vms_that_still_need_a_look(server: MCPServer) -> None:
    result = call(server, "scan", {"vcenters": ["vc-a"], "limit": 200})

    vms = by_name(result)
    assert vms["swap-01"]["state"] == "healthy"
    assert vms["swap-01"]["flags"] == ["memory_reclaimed"]
    assert vms["swap-01"]["values"]["swapped_mb"] == 2048
    assert vms["flaky-01"]["flags"] == ["heartbeat_intermittent"]
    assert vms["alarm-01"]["flags"] == ["vcenter_alarm"]
    alarm = vms["alarm-01"]["values"]["alarms"][0]
    assert alarm["status"] == "red"
    assert alarm["alarm"]
    assert alarm["alarm"] != "alarm-11"  # resolved to its name
    assert result["counts_by_flag"]["memory_reclaimed"] == 1
    assert any("memory_reclaimed" in finding for finding in result["findings"])


def test_a_leftover_vm_is_flagged_long_running(server: MCPServer) -> None:
    result = call(server, "scan", {"states": ["long_running"]})

    assert [(vm["vcenter"], vm["name"]) for vm in result["abnormal_vms"]] == [("vc-a", "left-01")]
    assert result["abnormal_vms"][0]["age_hours"] > 25


def test_memory_reclaim_is_weighed_as_a_cause(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1004", "vm_name": "swap-01", "console_captures": 0},
    )

    assert result["conclusion"]["causes"][0]["cause"].startswith("memory pressure")
    assert "memory_reclaimed" in result["conclusion"]["flags"]


def test_no_tools_is_explained_in_the_finding(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1004", "vm_name": "notools-01", "console_captures": 0},
    )

    assert result["machine"]["state"] == "no_tools"
    assert "Tools is not installed" in result["finding"]


def test_a_paused_vm_is_the_cause_of_itself(server: MCPServer) -> None:
    result = call(
        server,
        "diagnose_vm",
        {"vcenter": "vc-a", "env_id": "env-1004", "vm_name": "paused-01", "console_captures": 0},
    )

    assert result["conclusion"]["causes"][0]["cause"] == "the VM is paused"


def test_an_unknown_state_is_refused_with_the_choices(server: MCPServer) -> None:
    # In process the error is raised; an MCP client receives the same words as an error result.
    with pytest.raises(ToolError, match="unknown states or flags") as raised:
        asyncio.run(server.call_tool("scan", {"states": ["sleepy"]}))

    assert not isinstance(raised.value, UnexpectedToolError)
    assert "long_running" in str(raised.value)


def test_an_unreachable_vcenter_is_said_in_words(settings: Settings) -> None:
    broken = settings.model_copy(
        update={"vcenters": (VCenter(name="vc-gone", host="127.0.0.1", port=1),), "timeout_seconds": 5.0}
    )
    server = build_server(broken)

    with pytest.raises(ToolError, match="unreachable") as raised:
        asyncio.run(server.call_tool("diagnose_vm", {"vcenter": "vc-gone", "moref": "vm-1"}))

    assert not isinstance(raised.value, UnexpectedToolError)


# -- environments that have lived too long ---------------------------------------------------


def folders(result: dict[str, Any]) -> list[tuple[str, str]]:
    return [(entry["vcenter"], entry["folder"]) for entry in result["environments"]]


def test_old_environments_are_found_anywhere_oldest_first(server: MCPServer) -> None:
    result = call(server, "find_old_environments", {"older_than_hours": 5})

    assert folders(result) == [
        ("vc-a", "/DC0/vm/environments/env-0999"),
        ("vc-b", "/DC0/vm/projects/env-2001"),
        ("vc-b", "/DC0/vm/projects/team-x/env-3001"),
    ]
    oldest = result["environments"][0]
    assert oldest["age_hours"] > 25
    assert oldest["powered_on"] == 1
    assert oldest["parent"] == "environments"
    two = result["environments"][1]
    assert (two["vms"], two["environment"]) == (2, "env-2001")
    assert two["newest_age_hours"] < two["age_hours"]
    assert "2 of them still have powered-on VMs" in result["findings"]


def test_under_narrows_by_a_segment_at_any_depth(server: MCPServer) -> None:
    result = call(server, "find_old_environments", {"older_than_hours": 5, "under": ["projects/"]})

    assert folders(result) == [
        ("vc-b", "/DC0/vm/projects/env-2001"),
        ("vc-b", "/DC0/vm/projects/team-x/env-3001"),
    ]


def test_under_takes_a_run_of_segments_too(server: MCPServer) -> None:
    result = call(server, "find_old_environments", {"older_than_hours": 5, "under": ["projects/team-x"]})

    assert folders(result) == [("vc-b", "/DC0/vm/projects/team-x/env-3001")]
    assert result["environments"][0]["states"] == {"off": 1}


def test_under_environments_on_one_vcenter(server: MCPServer) -> None:
    result = call(
        server,
        "find_old_environments",
        {"older_than_hours": 1, "under": ["environments"], "vcenters": ["vc-a"]},
    )

    assert folders(result) == [("vc-a", "/DC0/vm/environments/env-0999")]


def test_vms_outside_any_environment_are_marked(server: MCPServer) -> None:
    result = call(server, "find_old_environments", {"older_than_hours": 0, "vcenters": ["vc-a"]})

    root = [entry for entry in result["environments"] if entry["folder"] == "/DC0/vm"]
    assert root
    assert root[0]["root_vm_folder"] is True
    assert all(
        not entry["root_vm_folder"] for entry in result["environments"] if entry["folder"] != "/DC0/vm"
    )
