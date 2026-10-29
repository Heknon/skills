"""What a VM's state says, judged against the thresholds. Pure: facts in, verdicts out.

A check never hides the number it judged: every verdict carries the values it
was decided on, so a reader can disagree with a threshold without re-reading
vCenter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from vsphere_mcp.config import Thresholds
    from vsphere_mcp.inventory import VmFacts

# The states a VM can be in, worst first. A VM has exactly one.
INACCESSIBLE = "inaccessible"
BLOCKED_ON_QUESTION = "blocked_on_question"
HUNG = "hung"
BUSY_NOT_UP = "busy_not_up"
BOOTED_NOT_UP = "booted_not_up"
LOST_HEARTBEAT = "lost_heartbeat"
NO_BOOT_TIME = "no_boot_time"
BOOTING = "booting"
HEALTHY = "healthy"
OFF = "off"

ABNORMAL = (
    INACCESSIBLE,
    BLOCKED_ON_QUESTION,
    HUNG,
    BUSY_NOT_UP,
    BOOTED_NOT_UP,
    LOST_HEARTBEAT,
    NO_BOOT_TIME,
)
STATES = (*ABNORMAL, BOOTING, HEALTHY, OFF)

MEANING = {
    INACCESSIBLE: "vCenter cannot reach or account for the VM",
    BLOCKED_ON_QUESTION: "the VM waits on a pending question and does nothing until it is answered",
    HUNG: ("booted long ago, Tools never came up, and the VM uses almost no CPU: it is waiting on something"),
    BUSY_NOT_UP: (
        "booted long ago, Tools never came up, and the VM is burning CPU: starved, spinning or still working"
    ),
    BOOTED_NOT_UP: "booted long ago and Tools never came up",
    LOST_HEARTBEAT: "Tools runs, but its heartbeat to vCenter has stopped",
    NO_BOOT_TIME: "powered on, but vCenter reports no boot time to judge it by",
    BOOTING: "powered on recently; Tools not up yet, which is normal this early",
    HEALTHY: "powered on with Tools running",
    OFF: "powered off or suspended",
}

# Flags ride alongside the state; a VM may carry several.
BOOT_LOOP = "boot_loop"
CONSOLIDATION_NEEDED = "consolidation_needed"
TOOLS_FLAPPING = "tools_flapping"

RESET_EVENTS = (
    "VmResettingEvent",
    "VmGuestRebootEvent",
    "VmDasBeingResetEvent",
    "VmDasBeingResetWithScreenshotEvent",
)


@dataclass
class Verdict:
    """One VM's state, why, and on which values."""

    state: str
    reasons: list[str]
    values: dict[str, Any]
    flags: list[str] = field(default_factory=list)

    @property
    def abnormal(self) -> bool:
        """Whether the state is one a person would want to look at."""
        return self.state in ABNORMAL or bool(self.flags)

    def as_dict(self) -> dict[str, Any]:
        """The verdict as a tool result shows it."""
        return {
            "state": self.state,
            "meaning": MEANING[self.state],
            "reasons": self.reasons,
            "flags": self.flags,
            "values": self.values,
        }


def classify(  # noqa: C901, PLR0911 - one decision list, kept in one place
    vm: VmFacts,
    thresholds: Thresholds,
    *,
    resets_in_window: int = 0,
) -> Verdict:
    """Judge one VM. The order is the order of precedence; the first match wins."""
    fraction = vm.cpu_fraction
    values: dict[str, Any] = {
        "power_state": vm.power_state,
        "connection_state": vm.connection_state,
        "uptime_minutes": _round(vm.uptime_minutes),
        "tools_running": vm.tools_running,
        "heartbeat": vm.heartbeat,
        "cpu_mhz": vm.cpu_mhz,
        "cpu_share_of_vcpus": _round(fraction, 3),
        "resets_in_window": resets_in_window,
    }
    flags = []
    if resets_in_window >= thresholds.boot_loop_resets:
        flags.append(BOOT_LOOP)
    if vm.consolidation_needed:
        flags.append(CONSOLIDATION_NEEDED)

    def verdict(state: str, *reasons: str) -> Verdict:
        if BOOT_LOOP in flags:
            reasons = (
                *reasons,
                (
                    f"{resets_in_window} resets or guest reboots in the last "
                    f"{thresholds.boot_loop_window_minutes:g} min"
                ),
            )
        return Verdict(state, list(reasons), values, flags)

    if vm.connection_state and vm.connection_state != "connected":
        return verdict(INACCESSIBLE, f"connection state is {vm.connection_state}")
    if vm.question is not None:
        values["question"] = vm.question.text
        values["choices"] = vm.question.choices
        return verdict(BLOCKED_ON_QUESTION, f"pending question: {vm.question.text}")
    if not vm.powered_on:
        return verdict(OFF, f"power state is {vm.power_state or 'unknown'}")
    if vm.tools_up:
        if vm.heartbeat == "red":
            return verdict(LOST_HEARTBEAT, "Tools running but heartbeat is red")
        if vm.heartbeat == "gray":
            # Gray beside a running Tools is the first seconds after it starts.
            return verdict(HEALTHY, "Tools running; heartbeat not reported yet (gray)")
        return verdict(HEALTHY, "Tools running")
    if vm.uptime_minutes is None:
        return verdict(NO_BOOT_TIME, "powered on, Tools not running, and no boot time reported")
    if vm.uptime_minutes < thresholds.booted_not_up_minutes:
        return verdict(
            BOOTING,
            f"booted {vm.uptime_minutes:.1f} min ago, under the "
            f"{thresholds.booted_not_up_minutes:g} min allowed before Tools is expected",
        )
    up = f"booted {vm.uptime_minutes:.0f} min ago and Tools is {vm.tools_running or 'unreported'}"
    if vm.cpu_mhz is not None and vm.cpu_mhz <= thresholds.hung_cpu_mhz:
        return verdict(HUNG, up, f"CPU {vm.cpu_mhz:.0f} MHz, at or under {thresholds.hung_cpu_mhz:g} MHz")
    if fraction is not None and fraction >= thresholds.busy_cpu_fraction:
        return verdict(
            BUSY_NOT_UP,
            up,
            f"CPU at {fraction:.0%} of its {vm.num_cpu} vCPU(s), at or over "
            f"{thresholds.busy_cpu_fraction:.0%}",
        )
    return verdict(BOOTED_NOT_UP, up)


def host_pressure(
    capacity_mhz: float | None,
    demand_mhz: float | None,
    usage_mhz: float | None,
    thresholds: Thresholds,
) -> dict[str, Any]:
    """A host's CPU demand against its capacity, from perf when it has it.

    Demand is what the VMs asked for; usage is what they got. Above 100% demand
    the host is overcommitted and its VMs wait (ready time). When only usage is
    known it is reported as such, since usage cannot exceed capacity and so
    understates exactly the case this check exists for.
    """
    basis = "demand" if demand_mhz is not None else "usage" if usage_mhz is not None else None
    value = demand_mhz if demand_mhz is not None else usage_mhz
    percent = (value / capacity_mhz * 100) if value is not None and capacity_mhz else None
    over = percent is not None and percent >= thresholds.host_cpu_demand_percent
    return {
        "basis": basis,
        "percent_of_capacity": _round(percent, 1),
        "capacity_mhz": capacity_mhz,
        "mhz": value,
        "overcommitted": bool(over and basis == "demand"),
        "near_capacity": bool(over and basis == "usage"),
        "threshold_percent": thresholds.host_cpu_demand_percent,
    }


def ready_percent(ready_ms: float, interval_seconds: int, vcpus: int) -> float:
    """CPU ready as a percent of the sample, per vCPU.

    `cpu.ready.summation` is milliseconds spent ready but not running, summed
    over the interval and over the VM's vCPUs; raw, it misleads.
    """
    return ready_ms / (interval_seconds * 1000 * max(vcpus, 1)) * 100


def resets_by_vm(events: list[Any], window_minutes: float, now: Any) -> dict[str, int]:
    """How many reset-like events each VM had inside the window, by moref."""
    counts: dict[str, int] = {}
    for event in events:
        if type(event).__name__.rsplit(".", 1)[-1] not in RESET_EVENTS:
            continue
        if (now - event.createdTime).total_seconds() > window_minutes * 60:
            continue
        vm = getattr(getattr(event, "vm", None), "vm", None)
        if vm is not None:
            moref = vm._moId  # noqa: SLF001
            counts[moref] = counts.get(moref, 0) + 1
    return counts


def count_states(verdicts: Mapping[str, Verdict]) -> dict[str, int]:
    """How many VMs are in each state, in the order of `STATES`, zeros left out."""
    counts = dict.fromkeys(STATES, 0)
    for verdict in verdicts.values():
        counts[verdict.state] += 1
    return {state: count for state, count in counts.items() if count}


def _round(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)
