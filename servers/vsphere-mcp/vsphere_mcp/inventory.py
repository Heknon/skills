"""A vCenter's inventory as facts: VMs, the folders they live in, their hosts and disks.

The layout is discovered, never assumed. An environment is a folder named by its
Twix id; which parent groups it (environments, projects, anything else) is read
from the tree and reported, not expected. A VM is identified by its vCenter and
moref; its name means something only inside its folder.

Where vCenter's own data disagrees with itself (a boot time in one place and
not the other, a VM outside any folder) the disagreement is kept as a note on
the fact, for the reader to see, rather than smoothed over.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pyVmomi import vim

from vsphere_mcp.vcenter import as_utc

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from vsphere_mcp.vcenter import VCenterSession

VM_PATHS = (
    "name",
    "parent",
    "config.template",
    "config.instanceUuid",
    "config.createDate",
    "config.guestId",
    "config.guestFullName",
    "summary.config.numCpu",
    "runtime.powerState",
    "runtime.connectionState",
    "runtime.bootTime",
    "runtime.question",
    "runtime.host",
    "runtime.consolidationNeeded",
    "runtime.paused",
    "summary.runtime.bootTime",
    "summary.overallStatus",
    "summary.config.memorySizeMB",
    "summary.quickStats.guestMemoryUsage",
    "summary.quickStats.balloonedMemory",
    "summary.quickStats.swappedMemory",
    "summary.quickStats.compressedMemory",
    "triggeredAlarmState",
    "guest.toolsStatus",
    "summary.quickStats.overallCpuUsage",
    "summary.quickStats.uptimeSeconds",
    "summary.quickStats.guestHeartbeatStatus",
    "guest.toolsRunningStatus",
    "guest.toolsVersionStatus2",
    "guest.guestState",
    "guest.guestFamily",
    "guest.ipAddress",
    "datastore",
)
DEVICE_PATH = "config.hardware.device"
HOST_PATHS = (
    "name",
    "parent",
    "runtime.connectionState",
    "runtime.inMaintenanceMode",
    "summary.hardware.cpuMhz",
    "summary.hardware.numCpuCores",
    "summary.hardware.memorySize",
    "summary.quickStats.overallCpuUsage",
    "summary.quickStats.overallMemoryUsage",
)
DATASTORE_PATHS = (
    "name",
    "summary.url",
    "summary.capacity",
    "summary.freeSpace",
    "summary.accessible",
    "summary.type",
)
FOLDER_PATHS = ("name", "parent", "childType")
DATACENTER_PATHS = ("name", "parent", "vmFolder")
CLUSTER_PATHS = ("name",)

RUNNING = "guestToolsRunning"
STARTING = "guestToolsExecutingScripts"
NOT_INSTALLED = "toolsNotInstalled"
# Above this uptime, a power-on-based measurement is worth cautioning about on a
# VM whose Tools is down: it may be a warm reboot vCenter did not see.
NOTE_UPTIME_MINUTES = 60.0
_BOOT_NOTE_PREFIX = "boot: "


@dataclass
class Question:
    """A pending VM question: the VM waits on it and does nothing else."""

    id: str
    text: str
    choices: list[str]


@dataclass
class VmFacts:
    """What one read of a VM says about it, flattened for the checks."""

    vcenter: str
    moref: str
    name: str
    folder: str | None = None
    folder_moref: str | None = None
    folder_path: str | None = None
    folder_parent: str | None = None
    datacenter: str | None = None
    instance_uuid: str | None = None
    created: datetime | None = None
    template: bool = False
    power_state: str | None = None
    connection_state: str | None = None
    boot_time: datetime | None = None
    power_on_time: datetime | None = None
    boot_source: str | None = None
    quickstats_uptime_seconds: int | None = None
    uptime_minutes: float | None = None
    question: Question | None = None
    consolidation_needed: bool = False
    paused: bool = False
    overall_status: str | None = None
    alarms: list[dict[str, Any]] = field(default_factory=list)
    memory_mb: int | None = None
    guest_memory_mb: int | None = None
    ballooned_mb: int | None = None
    swapped_mb: int | None = None
    compressed_kb: int | None = None
    read_at: datetime | None = None
    tools_status: str | None = None
    tools_running: str | None = None
    tools_version_status: str | None = None
    heartbeat: str | None = None
    guest_state: str | None = None
    ip_address: str | None = None
    guest_id: str | None = None
    guest_os: str | None = None
    os_family: str = "unknown"
    num_cpu: int | None = None
    cpu_mhz: float | None = None
    host: str | None = None
    host_moref: str | None = None
    host_core_mhz: float | None = None
    host_connection_state: str | None = None
    host_maintenance: bool = False
    host_memory_percent: float | None = None
    cluster: str | None = None
    datastores: list[str] = field(default_factory=list)
    disk_chain: list[list[str]] = field(default_factory=list)
    base_disk: str | None = None
    serial_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def key(self) -> dict[str, str]:
        """How every later call names this VM: vCenter and moref, never the name."""
        return {"vcenter": self.vcenter, "moref": self.moref}

    @property
    def powered_on(self) -> bool:
        """Whether vCenter says the VM is on."""
        return self.power_state == "poweredOn"

    @property
    def tools_up(self) -> bool:
        """Whether Tools reports running."""
        return self.tools_running == RUNNING

    @property
    def tools_installed(self) -> bool | None:
        """Whether Tools is installed at all; None when vCenter did not say."""
        if self.tools_status is None:
            return None
        return self.tools_status != NOT_INSTALLED

    @property
    def age_hours(self) -> float | None:
        """How long ago the VM was created, by vCenter's clock (vCenter 6.7 and later)."""
        if self.created is None or self.read_at is None:
            return None
        return max(0.0, (self.read_at - self.created).total_seconds() / 3600)

    @property
    def cpu_fraction(self) -> float | None:
        """CPU use as a share of the VM's own vCPUs, where the host's speed is known."""
        if self.cpu_mhz is None or not self.num_cpu or not self.host_core_mhz:
            return None
        return self.cpu_mhz / (self.num_cpu * self.host_core_mhz)

    def identity(self) -> dict[str, Any]:
        """The fields a reader needs to know which VM this is, and where."""
        return {
            "vcenter": self.vcenter,
            "moref": self.moref,
            "name": self.name,
            "instance_uuid": self.instance_uuid,
            "created": self.created,
            "age_hours": None if self.age_hours is None else round(self.age_hours, 2),
            "boot_time": self.boot_time,
            "boot_time_source": self.boot_source,
            "folder": self.folder,
            "folder_path": self.folder_path,
            "host": self.host,
            "cluster": self.cluster,
            "datastores": self.datastores,
            "base_disk": self.base_disk,
            "guest_os": self.guest_os,
            "os_family": self.os_family,
        }


@dataclass
class HostFacts:
    """One ESXi host as the checks need it."""

    moref: str
    name: str
    cluster: str | None
    connection_state: str | None
    maintenance: bool
    core_mhz: float | None
    cores: int | None
    cpu_usage_mhz: float | None
    memory_bytes: int | None = None
    memory_usage_mb: float | None = None

    @property
    def memory_percent(self) -> float | None:
        """Host memory in use as a percent of what it has."""
        if not self.memory_bytes or self.memory_usage_mb is None:
            return None
        return self.memory_usage_mb * 1024 * 1024 / self.memory_bytes * 100

    @property
    def capacity_mhz(self) -> float | None:
        """The host's CPU capacity: cores times speed."""
        if self.core_mhz is None or not self.cores:
            return None
        return self.core_mhz * self.cores


@dataclass
class FolderFacts:
    """One VM folder, with its full path from the datacenter."""

    moref: str
    name: str
    parent_moref: str | None
    path: str
    parent_name: str | None
    datacenter: str | None


@dataclass
class Inventory:
    """One read of a vCenter, at vCenter's own time."""

    vcenter: str
    read_at: datetime
    vms: list[VmFacts]
    hosts: dict[str, HostFacts]
    datastores: dict[str, dict[str, Any]]
    folders: dict[str, FolderFacts]
    base_disks_read: bool

    def vms_in_folder(self, folder_moref: str, *, nested: bool = True) -> list[VmFacts]:
        """The VMs in a folder, and in its subfolders unless told otherwise."""
        if not nested:
            return [vm for vm in self.vms if vm.folder_moref == folder_moref]
        inside = {folder_moref} | {moref for moref in self.folders if self._descends(moref, folder_moref)}
        return [vm for vm in self.vms if vm.folder_moref in inside]

    def _descends(self, moref: str, ancestor: str) -> bool:
        seen = set()
        current = self.folders.get(moref)
        while current is not None and current.moref not in seen:
            seen.add(current.moref)
            if current.parent_moref == ancestor:
                return True
            current = self.folders.get(current.parent_moref or "")
        return False


def os_family(guest_id: str | None, full_name: str | None, family: str | None) -> str:
    """Windows, Linux or other, from whichever of vCenter's three fields says so."""
    for text in (guest_id, full_name, family):
        lowered = (text or "").lower()
        if lowered.startswith("win") or "windows" in lowered:
            return "windows"
    for text in (guest_id, full_name, family):
        lowered = (text or "").lower()
        if any(
            mark in lowered
            for mark in (
                "linux",
                "rhel",
                "centos",
                "ubuntu",
                "debian",
                "sles",
                "oracle",
                "photon",
                "rocky",
                "alma",
            )
        ):
            return "linux"
    return "unknown"


def disk_chains(devices: Iterable[Any]) -> list[list[str]]:
    """Each virtual disk's chain, the VM's own file first and the base disk last."""
    chains = []
    for device in devices or []:
        if not isinstance(device, vim.vm.device.VirtualDisk):
            continue
        backing = device.backing
        chain: list[str] = []
        seen: set[str] = set()
        while backing is not None:
            name = getattr(backing, "fileName", None)
            if not name or name in seen:
                break
            seen.add(name)
            chain.append(name)
            backing = getattr(backing, "parent", None)
        if chain:
            chains.append(chain)
    return chains


def serial_files(devices: Iterable[Any]) -> list[str]:
    """Datastore files the VM's serial ports write to: where EMS or a kernel console lands."""
    files = []
    for device in devices or []:
        if not isinstance(device, vim.vm.device.VirtualSerialPort):
            continue
        backing = device.backing
        if isinstance(backing, vim.vm.device.VirtualSerialPort.FileBackingInfo) and backing.fileName:
            files.append(backing.fileName)
    return files


def read_folders(session: VCenterSession) -> dict[str, FolderFacts]:
    """Every folder with its path from its datacenter, read in two calls."""
    datacenters = session.retrieve(vim.Datacenter, DATACENTER_PATHS)
    rows = session.retrieve(vim.Folder, FOLDER_PATHS)
    raw = {row["moref"]: row for row in rows}
    datacenter_of_folder = {
        row["vmFolder"]._moId: row["name"]  # noqa: SLF001
        for row in datacenters
        if row.get("vmFolder") is not None
    }
    folders: dict[str, FolderFacts] = {}

    def build(moref: str, depth: int = 0) -> FolderFacts | None:
        if moref in folders:
            return folders[moref]
        row = raw.get(moref)
        if row is None or depth > 64:  # noqa: PLR2004 - a cycle guard, not a limit
            return None
        parent = row.get("parent")
        parent_moref = parent._moId if parent is not None else None  # noqa: SLF001
        datacenter = datacenter_of_folder.get(moref)
        parent_facts = build(parent_moref, depth + 1) if parent_moref in raw else None
        if datacenter is not None:
            path = f"/{datacenter}/{row['name']}"
        elif parent_facts is not None:
            path = f"{parent_facts.path}/{row['name']}"
            datacenter = parent_facts.datacenter
        else:
            path = f"/{row['name']}"
        facts = FolderFacts(
            moref=moref,
            name=row["name"],
            parent_moref=parent_moref,
            path=path,
            parent_name=parent_facts.name if parent_facts else None,
            datacenter=datacenter,
        )
        folders[moref] = facts
        return facts

    for moref in raw:
        build(moref)
    return folders


def read_hosts(session: VCenterSession) -> dict[str, HostFacts]:
    """Every host, with its cluster's name."""
    clusters = {row["moref"]: row["name"] for row in session.retrieve(vim.ComputeResource, CLUSTER_PATHS)}
    hosts = {}
    for row in session.retrieve(vim.HostSystem, HOST_PATHS):
        parent = row.get("parent")
        cluster = clusters.get(parent._moId) if parent is not None else None  # noqa: SLF001
        hosts[row["moref"]] = HostFacts(
            moref=row["moref"],
            name=row.get("name", row["moref"]),
            cluster=cluster,
            connection_state=row.get("runtime.connectionState"),
            maintenance=bool(row.get("runtime.inMaintenanceMode")),
            core_mhz=_number(row.get("summary.hardware.cpuMhz")),
            cores=row.get("summary.hardware.numCpuCores"),
            cpu_usage_mhz=_number(row.get("summary.quickStats.overallCpuUsage")),
            memory_bytes=row.get("summary.hardware.memorySize"),
            memory_usage_mb=_number(row.get("summary.quickStats.overallMemoryUsage")),
        )
    return hosts


def alarm_names(session: VCenterSession, rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    """The names of the alarms triggered on these VMs, read in one call."""
    refs = {}
    for row in rows:
        for state in row.get("triggeredAlarmState") or []:
            alarm = getattr(state, "alarm", None)
            if alarm is not None:
                refs[alarm._moId] = alarm  # noqa: SLF001
    if not refs:
        return {}
    named = session.retrieve(vim.alarm.Alarm, ("info.name",), objects=list(refs.values()))
    return {row["moref"]: row.get("info.name") or row["moref"] for row in named}


def read_datastores(session: VCenterSession) -> dict[str, dict[str, Any]]:
    """Every datastore by moref: name, url, capacity, free space, accessibility."""
    stores = {}
    for row in session.retrieve(vim.Datastore, DATASTORE_PATHS):
        stores[row["moref"]] = {
            "_ref": row["_ref"],
            "moref": row["moref"],
            "name": row.get("name"),
            "url": row.get("summary.url"),
            "capacity_bytes": row.get("summary.capacity"),
            "free_bytes": row.get("summary.freeSpace"),
            "accessible": row.get("summary.accessible"),
            "type": row.get("summary.type"),
        }
    return stores


def read_inventory(
    session: VCenterSession,
    *,
    with_devices: bool,
    vm_objects: Sequence[Any] | None = None,
    reboots: dict[str, datetime] | None = None,
    rebooted_at: datetime | None = None,
) -> Inventory:
    """Read a vCenter's VMs (all, or the given ones) and what they sit on.

    `reboots` maps a VM's moref to the most recent reboot/reset event vCenter
    logged for it; `rebooted_at` is a reboot time the caller knows from Sahara.
    Either overrides power-on time for the uptime judgement when it is newer.
    """
    read_at = session.now()
    folders = read_folders(session)
    hosts = read_hosts(session)
    datastores = read_datastores(session)
    paths = (*VM_PATHS, DEVICE_PATH) if with_devices else VM_PATHS
    rows = session.retrieve(vim.VirtualMachine, paths, objects=vm_objects)
    names = alarm_names(session, rows)
    vms = [
        vm_facts(
            session.vcenter.name,
            row,
            read_at,
            folders,
            hosts,
            datastores,
            with_devices=with_devices,
            alarms=names,
            reboots=reboots,
            rebooted_at=rebooted_at,
        )
        for row in rows
    ]
    return Inventory(
        vcenter=session.vcenter.name,
        read_at=read_at,
        vms=[vm for vm in vms if not vm.template],
        hosts=hosts,
        datastores=datastores,
        folders=folders,
        base_disks_read=with_devices,
    )


def vm_facts(  # noqa: C901, PLR0913, PLR0915 - one flattening of one row
    vcenter: str,
    row: dict[str, Any],
    read_at: datetime,
    folders: dict[str, FolderFacts],
    hosts: dict[str, HostFacts],
    datastores: dict[str, dict[str, Any]],
    *,
    with_devices: bool,
    alarms: dict[str, str] | None = None,
    reboots: dict[str, datetime] | None = None,
    rebooted_at: datetime | None = None,
) -> VmFacts:
    """Flatten one property-collector row into `VmFacts`, noting what disagrees."""
    facts = VmFacts(vcenter=vcenter, moref=row["moref"], name=row.get("name", row["moref"]), read_at=read_at)
    parent = row.get("parent")
    if parent is not None and isinstance(parent, vim.Folder):
        folder = folders.get(parent._moId)  # noqa: SLF001
        facts.folder_moref = parent._moId  # noqa: SLF001
        if folder is not None:
            facts.folder = folder.name
            facts.folder_path = folder.path
            facts.folder_parent = folder.parent_name
            facts.datacenter = folder.datacenter
    elif parent is None:
        facts.notes.append("vCenter reports no parent folder for this VM (it may belong to a vApp)")
    facts.instance_uuid = row.get("config.instanceUuid")
    created = row.get("config.createDate")
    facts.created = as_utc(created) if isinstance(created, datetime) else None
    facts.template = bool(row.get("config.template"))
    facts.power_state = row.get("runtime.powerState")
    facts.connection_state = row.get("runtime.connectionState")

    runtime_boot = row.get("runtime.bootTime")
    summary_boot = row.get("summary.runtime.bootTime")
    boot = runtime_boot or summary_boot
    if runtime_boot and summary_boot and abs((runtime_boot - summary_boot).total_seconds()) > 60:  # noqa: PLR2004
        facts.notes.append("runtime.bootTime and summary.runtime.bootTime disagree; used runtime.bootTime")
    facts.power_on_time = as_utc(boot) if boot is not None else None
    facts.quickstats_uptime_seconds = row.get("summary.quickStats.uptimeSeconds")

    question = row.get("runtime.question")
    if question is not None:
        choice = getattr(question, "choice", None)
        choices = [
            getattr(option, "label", None) or getattr(option, "key", "")
            for option in getattr(choice, "choiceInfo", None) or []
        ]
        facts.question = Question(id=str(question.id), text=question.text or "", choices=choices)
    facts.consolidation_needed = bool(row.get("runtime.consolidationNeeded"))
    facts.paused = bool(row.get("runtime.paused"))
    facts.overall_status = row.get("summary.overallStatus")
    facts.memory_mb = row.get("summary.config.memorySizeMB")
    facts.guest_memory_mb = row.get("summary.quickStats.guestMemoryUsage")
    facts.ballooned_mb = row.get("summary.quickStats.balloonedMemory")
    facts.swapped_mb = row.get("summary.quickStats.swappedMemory")
    facts.compressed_kb = row.get("summary.quickStats.compressedMemory")
    facts.alarms = [
        {
            "alarm": (alarms or {}).get(state.alarm._moId, state.alarm._moId),  # noqa: SLF001
            "status": state.overallStatus,
            "since": as_utc(state.time) if getattr(state, "time", None) else None,
            "acknowledged": bool(getattr(state, "acknowledged", False)),
        }
        for state in row.get("triggeredAlarmState") or []
        if getattr(state, "alarm", None) is not None
    ]
    facts.tools_status = row.get("guest.toolsStatus")
    facts.tools_running = row.get("guest.toolsRunningStatus")
    facts.tools_version_status = row.get("guest.toolsVersionStatus2")
    facts.heartbeat = row.get("summary.quickStats.guestHeartbeatStatus")
    facts.guest_state = row.get("guest.guestState") or None
    facts.ip_address = row.get("guest.ipAddress")
    facts.guest_id = row.get("config.guestId")
    facts.guest_os = row.get("config.guestFullName")
    facts.os_family = os_family(facts.guest_id, facts.guest_os, row.get("guest.guestFamily"))
    facts.num_cpu = row.get("summary.config.numCpu")
    facts.cpu_mhz = _number(row.get("summary.quickStats.overallCpuUsage"))

    host_ref = row.get("runtime.host")
    if host_ref is not None:
        host = hosts.get(host_ref._moId)  # noqa: SLF001
        facts.host_moref = host_ref._moId  # noqa: SLF001
        if host is not None:
            facts.host = host.name
            facts.host_core_mhz = host.core_mhz
            facts.cluster = host.cluster
            facts.host_connection_state = host.connection_state
            facts.host_maintenance = host.maintenance
            facts.host_memory_percent = host.memory_percent
    facts.datastores = [
        datastores.get(ref._moId, {}).get("name") or ref._moId  # noqa: SLF001
        for ref in row.get("datastore") or []
    ]
    if with_devices:
        devices = row.get(DEVICE_PATH) or []
        facts.disk_chain = disk_chains(devices)
        bases = sorted({chain[-1] for chain in facts.disk_chain if len(chain) > 1})
        if bases:
            facts.base_disk = bases[0]
            if len(bases) > 1:
                facts.notes.append(f"disks on {len(bases)} different base disks; grouped by {bases[0]}")
        facts.serial_files = serial_files(devices)
    if row.get("_missing"):
        facts.notes.append("vCenter withheld: " + ", ".join(row["_missing"]))
    set_effective_boot(facts, read_at, reboots=reboots, rebooted_at=rebooted_at)
    return facts


def set_effective_boot(
    facts: VmFacts,
    read_at: datetime,
    *,
    reboots: dict[str, datetime] | None = None,
    rebooted_at: datetime | None = None,
) -> None:
    """Measure uptime from the most recent reboot, not from power-on.

    runtime.bootTime only moves on a power cycle, never on an in-guest reboot, so
    for a warm-rebooted VM it is the original power-on, hours or days ago. The
    reboot vCenter actually saw (a reset or guest-reboot event), or the reboot
    time the caller knows from Sahara, is newer and is what the stuck/booting
    judgement must rest on. Called again by `diagnose_vm` once it has fetched
    the events, so a scan's power-on estimate is refined to the real reboot.
    """
    reported = as_utc(rebooted_at) if rebooted_at is not None else None
    event_reboot = (reboots or {}).get(facts.moref)
    candidates = [
        (when, source)
        for when, source in (
            (reported, "reported_reboot"),
            (event_reboot, "reboot_event"),
            (facts.power_on_time, "power_on"),
        )
        if when is not None
    ]
    facts.notes = [note for note in facts.notes if not note.startswith(_BOOT_NOTE_PREFIX)]
    if candidates:
        facts.boot_time, facts.boot_source = max(candidates, key=lambda item: item[0])
        facts.uptime_minutes = max(0.0, (read_at - facts.boot_time).total_seconds() / 60)
        if (
            facts.boot_source == "power_on"
            and facts.power_state == "poweredOn"
            and facts.tools_running != RUNNING
            and facts.uptime_minutes > NOTE_UPTIME_MINUTES
        ):
            facts.notes.append(
                _BOOT_NOTE_PREFIX
                + "uptime is from power-on; vCenter does not see an in-guest reboot, so if this VM "
                "was rebooted in the guest its uptime overstates how long it has been trying to "
                "boot — pass the reboot time, or read a reset/reboot event, to judge it"
            )
    elif facts.power_state == "poweredOn":
        uptime = facts.quickstats_uptime_seconds
        if isinstance(uptime, int) and uptime > 0:
            facts.uptime_minutes = uptime / 60
            facts.boot_source = "quickstats"
            facts.notes.append(
                _BOOT_NOTE_PREFIX + "no boot time reported; uptime from quickStats (power-on based)"
            )
        else:
            facts.notes.append(_BOOT_NOTE_PREFIX + "powered on, but vCenter reports no boot time")


def find_environment(
    folders: dict[str, FolderFacts],
    env_id: str,
    hints: Sequence[str] = (),
) -> list[FolderFacts]:
    """The folders that are this environment: exact name first, then names containing it.

    Folders under a hinted parent come first; the rest are still returned.
    """
    wanted = env_id.strip().lower()
    if not wanted:
        return []
    hinted = {hint.lower() for hint in hints}
    exact = [folder for folder in folders.values() if folder.name.lower() == wanted]
    candidates = exact or [folder for folder in folders.values() if wanted in folder.name.lower()]
    return sorted(
        candidates,
        key=lambda folder: (
            (folder.parent_name or "").lower() not in hinted if hinted else False,
            len(folder.path),
            folder.path,
        ),
    )


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None
