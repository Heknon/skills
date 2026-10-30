# vsphere-mcp

A read-only MCP server over the vCenters (and, optionally, vROps), for
diagnosing VMs that are stuck, did not come back after a reboot, or keep losing
VMware Tools. The plan it implements is `plans/vsphere-vrops-mcp.md`.

It answers two kinds of question:

- **From a Sahara VMware Tools error** (which names the vCenter, the machine
  and the Twix environment id): `diagnose_vm(vcenter, env_id, vm_name)` runs
  every check in a fixed order and ends in the likely cause.
- **About the fleet** ("anything stuck on these vCenters?"): `scan` judges
  every VM, groups the abnormal ones by what they share (host, datastore,
  linked-clone base disk, environment, ...) against their population, and
  `explain_group` says why a group is abnormal.

## Read-only, by construction

The accounts it may run with can write, so the guarantee is in the code, not
the account:

- Every vSphere call goes through `readonly.ReadOnlyStub`, which refuses any
  method not on `ALLOWED_METHODS` before a byte is sent. The list is 13
  methods: login and logout, the clock, property reads, container views,
  `QueryEvents`, `QueryPerf`, `BrowseDiagnosticLog` / `QueryDescriptions` and
  `SearchDatastore_Task` (which only lists files).
- Every HTTP request (`vmware.log` and serial files over `/folder`, the
  console over `/screen`) goes through `ensure_read_request`: GET only.
- The console is read through `/screen`, never `CreateScreenshot_Task`, which
  writes a PNG into the VM's folder.
- A test drives every tool against simulated vCenters and asserts that the
  methods sent are a subset of the list; another tries power, reset, answer,
  reconfigure, destroy and screenshot-to-datastore through a live session and
  expects each to be refused.

Nothing is created, changed, answered, powered or deleted, and the server
runs nothing in the background.

## Concepts, not constants

Nothing hard-codes a folder path, a log field or a naming pattern:

- An environment is a folder named by its Twix id. `find_environment` looks for
  it (exact name first, then names containing it) and reports where it found
  it and under which parent (environments, projects, anything). Several
  matches are reported, never guessed between.
  `VSPHERE_ENV_PARENT_HINTS` only orders the search.
- A VM is identified by `(vcenter, moref)`. Its name is looked up only inside
  its environment folder, since later environments reuse it.
- A vCenter answers to its name, host, the host's first label and any
  configured alias, so whatever spelling a Sahara log uses resolves.
- Group values carry their vCenter (`vc-a:DC0_H0`): two vCenters' hosts of the
  same name are different hosts.
- Every check returns the numbers it judged, beside its verdict; thresholds
  are defaults in `VSPHERE_THRESHOLDS`, tuned on real incidents.

## Install and configure

```sh
uv tool install ./servers/vsphere-mcp        # add [ocr] for console OCR (needs tesseract)
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `VSPHERE_VCENTERS` | none | JSON list: `[{"name": "vc-04", "host": "vc04.example", "port": 443, "aliases": ["vc04-old"]}]`; per-vCenter `username` / `password` override the shared ones |
| `VSPHERE_USERNAME`, `VSPHERE_PASSWORD` | none | shared credentials |
| `VSPHERE_CA_BUNDLE` | system | PEM bundle for an internal CA |
| `VSPHERE_TLS_VERIFY` | `1` | `0` only against a simulator; warned about |
| `VSPHERE_ENV_PARENT_HINTS` | none | folder names to look under first, e.g. `environments,projects` |
| `VSPHERE_THRESHOLDS` | see `config.Thresholds` | JSON object overriding any threshold |
| `VSPHERE_SCAN_BASE_DISKS` | `1` | read disk chains in a scan, to group linked clones by base disk |
| `VSPHERE_TIMEOUT_SECONDS` | `60` | deadline per vCenter read |
| `VSPHERE_MAX_CONCURRENT_TOOLS` | `4` | tool calls at once |
| `VSPHERE_MAX_CONCURRENT_PER_VCENTER` | `4` | reads at once per vCenter |
| `VSPHERE_MAX_LOG_BYTES` | 4 MiB | how much of the end of a log is read |
| `VSPHERE_MAX_LOG_LINES` | `400` | most lines one result returns |
| `VSPHERE_VROPS_URL`, `VSPHERE_VROPS_USERNAME`, `VSPHERE_VROPS_PASSWORD`, `VSPHERE_VROPS_AUTH_SOURCE` | none | vROps; its tools appear only when set |

An MCP client config, over stdio:

```json
{
  "mcpServers": {
    "vsphere": {
      "command": "vsphere-mcp",
      "env": {
        "VSPHERE_VCENTERS": "[{\"name\": \"vc-01\", \"host\": \"vc01.example\"}]",
        "VSPHERE_USERNAME": "svc-readonly@vsphere.local",
        "VSPHERE_PASSWORD": "...",
        "VSPHERE_CA_BUNDLE": "/etc/pki/internal-ca.pem",
        "VSPHERE_ENV_PARENT_HINTS": "environments,projects"
      }
    }
  }
}
```

Or shared over HTTP, beside the Sahara MCP:
`vsphere-mcp --transport streamable-http --host 0.0.0.0 --port 8000 --allowed-host vsphere-mcp.example`
(`/healthz` for probes). Over HTTP every caller shares the configured
credential, which is read-only in effect either way.

A dedicated vCenter role is still worth creating where the account allows it,
so the guarantee holds twice: read inventory, console screen read (confirm
the privilege `/screen` needs on your version), datastore browse and file
read, and diagnostics (host logs).

## Tools

| Tool | Answers |
| --- | --- |
| `list_vcenters` | which vCenters, reachable, version, clock |
| `check_vcenters` | reachability, login time and open-session count per vCenter, for when the vCenter API itself is failing (SSL EOF, resets) — the sign of connection/session exhaustion |
| `vcenter_sessions` | a vCenter's open sessions grouped by user, source IP and client, with idle counts and the oldest — finds the client leaking sessions behind the exhaustion |
| `scan` | abnormal VMs on some or all vCenters, grouped by what they share; hosts over the CPU threshold and slow storage right now |
| `explain_group` | what a scan group's abnormal VMs share that the healthy ones beside them do not; CPU and storage over its boot window |
| `find_old_environments` | environments older than N hours (the age of their oldest VM), optionally only under `projects`, `environments`, `projects/team-x` or any other path segments, oldest first, with their VMs' states |
| `diagnose_window` | resets, failed power-ons, host CPU and storage over a past window, when VMs may be gone |
| `find_environment` | where an environment's folder is, on which vCenter(s), and its VMs |
| `diagnose_vm` | one VM: machine, CPU, storage, environment, boot timeline, serial console (EMS), console; the likely cause with evidence for and against |
| `diagnose_environment` | every VM of an environment, grouped, with CPU and storage |
| `get_boot_timeline` | how far the last boot got, from `vmware.log`, plus the serial console |
| `read_vm_log` | `vmware.log` / `vmware-N.log` lines, filtered on the server |
| `read_serial_console` | Windows EMS or a Linux kernel console, when the VM has a serial port to a file; stop codes with the layer each points at |
| `get_vm_console` | the screen in words: black, frozen or changing, blue screen, OCR text and the boot screen it shows |
| `get_vm_events` | a VM's events, by moref (a destroyed VM is reported as such) |
| `get_vm_hardware` | the VM's virtual devices (adapters, controllers, disks, CD-ROM, sound, serial, USB, video) and vCenter's connection view; flags a down boot NIC, a mounted ISO or a device error |
| `find_vms_by_device` | every VM across the vCenters that has, or lacks, a device — by category (sound, ethernet, usb, ...) or a kind substring (Vmxnet3, HdAudioCard); scoped with vcenters/under |
| `hardware_profile` | the whole fleet's virtual hardware generically: counts per category and kind, NIC-type breakdown, and the VMs that differ from their environment's norm |
| `find_vms_by_snapshot` | VMs with snapshots across the vCenters, biggest first — delta + memory-state size, oldest age, redo-chain depth, and consolidation-needed; the fleet view that catches a forgotten 50 GB snapshot |
| `get_host_health` | a host's CPU demand against capacity, its storage, its VMs |
| `get_datastore_health` | a datastore's latency and IOPS from every host mounting it, its VMs |
| `read_host_log` | `vmkernel` / `hostd` / `vpxa` lines, filtered |
| `vrops_*` | find a resource, list its stat keys, read stats, compare a window with previous days, alerts |

### States and flags

Every VM gets exactly one state, from the bulk read alone:

| State | Means |
| --- | --- |
| `inaccessible` | vCenter cannot reach or account for it |
| `blocked_on_question` | waiting on a VM question |
| `paused` | powered on, but the hypervisor is not running it |
| `hung` | booted over 10 min ago, Tools never up, almost no CPU |
| `busy_not_up` | the same, but burning CPU: starved, spinning or still working |
| `booted_not_up` | booted over 10 min ago, Tools never up (or stuck running its startup scripts) |
| `lost_heartbeat` | Tools runs, heartbeat red |
| `no_boot_time` | powered on, no boot time reported |
| `no_tools` | Tools not installed: not counted as stuck; judged by CPU, console and boot log |
| `booting` | booted recently, normal so far |
| `healthy`, `suspended`, `off` | as named |

Flags ride beside the state. Those that matter alone (counted as abnormal):
`boot_loop`, `tools_flapping`, `heartbeat_intermittent` (yellow heartbeat:
Tools may be crashing), `memory_reclaimed` (ballooned, swapped or compressed),
`host_memory_pressure`, `vcenter_alarm` (a red alarm, by name),
`host_not_connected`, `long_running` (older than `long_running_hours`, 24 by
default), `consolidation_needed`. Those that only add detail:
`host_in_maintenance`, `tools_outdated`. `scan(states=[...])` selects any
state or flag, for example `["no_tools"]` or `["long_running"]`.

The bulk read asks for about 35 properties per VM. A property an older vCenter
does not have is dropped and the read retried, rather than failing the scan,
and the result names what was dropped.

Results lead with `finding` / `findings`, keep the raw values, say what was
not read (`not_checked`, `available: false` with a reason), and are bounded to
fit a context window.

## What the diagnoses rest on

- **CPU starvation**: the VM's `cpu.ready.summation` as a percent per vCPU,
  and the host's `cpu.demand.average` against cores x MHz. Demand over 100% is
  overcommit; usage alone is reported as such, since it cannot exceed 100%.
- **Storage**: the hosts' `datastore.total{Read,Write}Latency` for the VM's
  datastores, `disk.{device,kernel,queue}Latency`, aborts and resets per
  device. High device latency points at the array (PowerFlex), high queue
  latency at the host's own queue.
- **The environment**: whether the healthy VMs beside a stuck one share its
  host, datastore and base disk (which argues against them) or not.
- **The boot**: `vmware.log` is the hypervisor's log, not the guest's. It shows
  how far a boot got (power-on or reset, firmware, first disk I/O, drivers,
  Tools), never the guest kernel's own words.
- **The guest's words**, when present: a serial port writing to a file
  (Windows EMS, a Linux kernel console) and the console screen. A VM without
  them is normal and the result says so.

## Testing

```sh
pip install -e './servers/vsphere-mcp[dev]'
pytest servers/vsphere-mcp          # unit tests, then the integration tests if Docker is there
ruff check servers/vsphere-mcp && ruff format --check servers/vsphere-mcp
```

The integration tests build two simulated vCenters in Docker with
`vmware/vcsim:v0.52.0` and `vmware/govc:v0.52.0`. One uses the environments
layout and one the projects layout. They hold linked clones, stuck Windows
and Linux VMs, a pending question, a boot loop, an EMS stop code, an
environment id present on both vCenters and machine names reused across
environments. For an air-gapped machine, `docker save` both images and
`docker load` them there.

What the simulator cannot do, and how the tests deal with it:

- Its performance counters are random, so CPU and storage numbers come from a
  controlled fake of `VCenterSession.perf`. Everything else (inventory,
  folders, disk chains, serial ports, events, files) is read from vcsim.
- It has no `/screen` endpoint. The 404 path is tested against it; the image
  analysis is tested with generated screenshots.
- It has no host logs. That path is tested as "unavailable, said so".

## To confirm on a real vCenter

- The privilege `/screen` needs, and what it returns for a black console.
- The statistics level: what `QueryPerf` keeps past the realtime hour.
- The datastore counter instances (volume id from `ds:///vmfs/volumes/<id>/`).
  The datastore name and the last part of the URL are tried after it.
- The `vmware.log` lines a real stuck boot, a stun and an APD leave. The
  patterns in `vmlog.py` are heuristics, and every match is returned with
  its line.
- What EMS writes to the serial port on the Windows versions in the fleet.
- The vROps stat keys on your version. `vrops_list_stat_keys` reads them.
- Snapshot sizes: the simulator reports them as 0, so the delta/memory-state
  accounting from `layoutEx` is unit-tested only; confirm the GB figures and the
  `Sessions.View` privilege for sessions against a real vCenter.
- That a guest reboot in your fleet logs a reset or guest-reboot event (so
  uptime is measured from the reboot, not power-on); if some reboots are
  silent to vCenter, pass `rebooted_at` from Sahara. The simulator cannot
  exercise this — the logic is covered by unit tests only.
- The `dcPath` for a datacenter that sits inside a folder, and a datastore
  name shared across two datacenters. The simulator has one flat datacenter,
  so these paths (full datacenter inventory path, datastore identity by moref)
  are correct by construction but unverified live.
- Whether `/folder` honours a suffix `Range` request; when it does not, a log
  larger than `VSPHERE_MAX_DOWNLOAD_BYTES` is reported as un-tailable rather
  than pulled whole.
