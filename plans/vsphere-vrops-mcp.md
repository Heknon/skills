# Plan: vSphere and vROps for incident diagnosis (an MCP and a skill)

Status: proposal. Nothing is built. Section 11 lists the open questions.

## 1. What it is

Today an agent investigating a broken Sahara environment can read two of
the four layers: Sahara (the Sahara MCP) and Sims/Twix (their logs in
Elastic). When the trail reaches the VMs, a person takes over: opens the
vCenter, finds the machine, looks at the console, browses the datastore
for `vmware.log`, checks the host and the storage. This plan puts those
steps in the agent's reach:

- **`vsphere-mcp`**: an MCP server over the nine vCenters, vROps and,
  optionally, PowerFlex. **Read-only, with no exceptions**: it looks things
  up and diagnoses. It powers nothing on or off, answers no VM question,
  creates, moves, reconfigures or deletes nothing, and writes no file on
  any datastore. It is not a service that runs on its own either: it
  answers when the agent asks, like the Sahara MCP.
- **`vm-incident` skill**: the procedure from a Sahara VMware Tools error
  to a verdict, through Sims logs, vCenter, vROps and PowerFlex, with the
  causes seen so far and the evidence that separates them.

## 2. The fleet, and how a machine is found

- **Environments are short-lived.** Sims/Twix creates an environment's VMs
  on one of the nine vCenters and destroys them after 10 minutes to 24
  hours. A VM name is reused by later environments, so a name alone never
  identifies a machine.
- **The Twix environment id is the anchor.** Each environment is a folder
  under the projects/environments folders on its vCenter, so the
  environment's VMs are the VMs in that folder.
- **Sahara already holds the way in.** Its VMware Tools error logs carry,
  in their extra data, the vCenter, the machine name and the environment
  id. From those three the MCP goes straight to the machine: vCenter →
  environment folder → VM by name inside it. Within one environment's
  folder a name is unique; across environments it is not, and the MCP
  never searches by name outside the folder.
- **Once found, the key is `(vcenter, moref)`**, with `instanceUuid` and
  `config.createDate` alongside. Every later call uses that key. If the
  VM has since been destroyed, the tool says *destroyed* and does not fall
  back to another VM with the same name.
- **A destroyed environment leaves less behind.** `vmware.log`, the
  console and the live state go with the VM. vCenter's events and tasks
  (for its retention period), host and datastore counters, vROps and
  PowerFlex history remain. The tools say which of these a diagnosis
  rested on.

## 3. The incident it is built around

The recurring symptom: Sahara reports VMware Tools errors after a reboot,
because the VM did not come back in time. Two causes found behind it so
far:

- **ESXi CPU overcommitted**: hosts at around 120% CPU demand. A booting
  VM waits for CPU constantly (ready time), so a 60-second boot takes ten
  minutes and Tools start after Sims or Sahara gave up. Often the VM is
  starved, not hung, and comes up later on its own.
- **PowerFlex saturated**: very high IOPS on the storage. A booting guest
  reads its disk hard; with device latency in the hundreds of
  milliseconds the bootloader and kernel stall, and a long stall looks
  like a hang on the console.

The flow, once this exists:

1. **Sahara**: the VMware Tools error log gives vCenter `vc-04`, machine
   `web-01`, environment `env-8812`, and the time.
2. **`diagnose_vm(vcenter="vc-04", env_id="env-8812", vm_name="web-01")`**,
   one call:
   - *machine*: powered on, booted 14 minutes ago, Tools not running,
     heartbeat gray, no pending question, CPU at 100% of one vCPU;
   - *console*: two captures 10 s apart, not black, changing (the guest is
     doing something);
   - *`vmware.log`*: the reset at 02:13:05, firmware handover, guest
     activity since;
   - *host `esx-31`*: CPU demand 118% of capacity for the last 40 minutes;
     this VM's ready time 38% per vCPU during boot;
   - *datastore*: latency normal;
   - *environment*: 4 of the 6 VMs in `env-8812` are in the same state,
     all on `esx-31` and `esx-32`, both above 110% demand; the 2 healthy
     ones are on `esx-40`.
   - *finding*: CPU starvation on `esx-31` and `esx-32`; the VM is booting
     slowly, not hung.
3. **vROps**: the cluster's demand over the past week: was this a spike
   or the normal state of the cluster?
4. **Verdict** (from the skill): the Tools error is a timeout on a VM
   starved of CPU on two overcommitted hosts; the environment and its
   template are not the cause, because its VMs on another host booted
   normally. Next check: why those hosts are above capacity (placement,
   or what else runs on them).

For the PowerFlex case, the same call reports the datastore's device
latency high in the boot window and, with the PowerFlex adapter, the
storage pool behind it and its IOPS.

## 4. The layers

| Layer | Owner | Agent access today | Holds |
| --- | --- | --- | --- |
| Sahara | application | Sahara MCP | the Tools error with vCenter, machine name and env id; the time of each step |
| Sims / Twix | infrastructure | logs in Elastic | what Sims asked the vCenter and when, its errors, timeouts |
| vCenter ×9 | bare metal | **none** | the environment folder and its VMs, live state, console, `vmware.log`, events and tasks, host and datastore counters |
| vROps | bare metal | **none** | history of hosts, clusters and datastores; alerts |
| PowerFlex | storage | **none** | volumes, pools, storage nodes, their IOPS and latency, rebuilds |

## 5. The options

| Option | What it is | For | Against |
| --- | --- | --- | --- |
| A. Skill + `govc` | a skill whose recipes run `govc` (one static Go binary) per vCenter | usable within days | the model holds vCenter credentials; raw JSON floods the context; nothing enforces read-only; the CPU and storage checks are many commands to get right in order |
| B. MCP only | typed read-only tools over pyVmomi, the vROps REST API and the PowerFlex REST API | read-only enforced; lookup and checks done once, correctly | no procedure for reading the results |
| **C. Both (recommended)** | the MCP for access and diagnosis, the skill for the procedure | each does what it is good at | two things to maintain |
| D. Adopt a community server | `vcenter-mcp`, `vSphere-MCP-Pro`, `mcvsphere`, `vcf-ops-mcp` | they exist | built for lifecycle (create, power, snapshot): exactly the actions this must not have; single vCenter; no console, log or contention diagnosis |

**Recommendation: C, built in the Sahara MCP's style** (package layout,
`pydantic-settings` config, stdio and Streamable HTTP, byte budgets,
concurrency limit). `govc` with a read-only account is useful in phase 0
to collect real examples before the server exists.

## 6. The tools

All read-only. Every result names the vCenter, the moref, the
`instanceUuid`, the creation time and the time it was read.

### 6.1 Finding

| Tool | Answers | API |
| --- | --- | --- |
| `list_vcenters` | the nine, reachable or not, their versions | `ServiceInstance.content.about` |
| `get_environment(vcenter, env_id)` | the environment's folder and every VM in it, with power state, Tools state, host, datastore, boot time | `ContainerView` on the folder + `PropertyCollector` |
| `find_environment(env_id)` | which vCenter holds the environment, when the log did not say | the env folder looked up on each vCenter |
| `get_vm(vcenter, env_id, vm_name)` | the VM's key | inside the env folder only |

### 6.2 The composite diagnoses

| Tool | Answers |
| --- | --- |
| **`diagnose_vm(vcenter, env_id, vm_name)`** | the flow of section 3, step 2: machine, console, `vmware.log`, host, datastore, the rest of the environment, a finding |
| **`diagnose_environment(vcenter, env_id)`** | every VM of the environment classified (healthy, starved, stuck, blocked on a question, off), grouped by host and datastore, the CPU and storage checks for each group, a finding |
| `diagnose_window(vcenters, since, until)` | the fleet view for when many environments failed at once: the env folders with affected VMs, grouped by host, cluster and datastore, with the CPU and storage checks |

Each composite runs the checks in a fixed order, with thresholds in
config tuned on past incidents, so the answer does not depend on the
model remembering what to look at:

1. **The machine**: power, Tools, heartbeat, pending question, uptime,
   CPU use. "Booted 14 min ago, Tools not running, CPU at one full vCPU"
   is starved or spinning; "CPU near zero" is hung; a question is blocked.
2. **CPU**: the host's demand against capacity, the VM's ready time and
   co-stop during boot. Above thresholds: *CPU starvation*, hosts named.
3. **Storage**: the datastore's device, kernel and queue latency, IOPS,
   aborted commands and resets in the boot window; with PowerFlex
   configured, the pool and nodes behind it. Above thresholds: *storage
   saturation*, datastore and pool named. High queue latency with normal
   device latency points at the host's queue; high device latency points
   at PowerFlex.
4. **The rest of the environment and its hosts**: are the healthy VMs on
   other hosts or datastores? That is what makes the finding a cause rather
   than a coincidence.
5. **Neither**: CPU and storage healthy, so the guest itself: console,
   `vmware.log`, events. Said explicitly.

A third recurring cause, once found, becomes a sixth check.

### 6.3 The pieces, to drill into one finding

| Tool | Answers | API |
| --- | --- | --- |
| `get_vm_state(key)` | power, connection, pending question, uptime, boot time, firmware, snapshots | `runtime`, `config` |
| `get_vm_guest(key)` | Tools running and version status, heartbeat, guest IPs, guest OS | `guest`, `guestHeartbeatStatus` |
| `get_vm_console(key, captures=2, interval_s=10)` | the console as an image, plus text for a model without vision: black fraction, frozen or changing, OCR if an engine is installed | the `/screen?id=` endpoint; **not** `CreateScreenshot_Task`, which writes a PNG into the VM's datastore folder |
| `get_vm_events(key, since)` | power, reset, migration, HA, reconfigure, Tools and guest events; works for destroyed VMs | `EventManager.QueryEvents` |
| `get_vm_tasks(key, since)` | tasks against it, Sims' included | `TaskManager` collectors |
| `read_vm_log(key, which=0, grep, tail, since)` | `vmware.log` and the rotated `vmware-N.log` from before the reboot, filtered on the server | HTTPS `GET /folder/<path>?dcPath=&dsName=` |
| `get_vm_metrics(key, counters, since)` | ready time, co-stop, CPU use, disk latency for this VM | `PerfManager.QueryPerf` |
| `get_host_health(host, since)` | CPU demand and usage, memory, per-datastore latency, the VMs on it | `PerfManager`, `summary` |
| `get_datastore_health(ds, since)` | free space, accessibility, latency, IOPS, the VMs on it | same |
| `read_host_log(host, log, since, grep)` | `vmkernel`, `hostd` lines in the window: path failures, APD/PDL, latency warnings | `DiagnosticManager.BrowseDiagnosticLog` |

Logs are never returned whole: a `grep`, `tail` or time window is
required, results are capped, and the default `grep` is a list of lines
that matter in a boot hang, built from your own logs in phase 0.

Counters behind the CPU and storage checks (to confirm against your
vCenter's statistics level): `cpu.ready.summation`, `cpu.costop.summation`,
`cpu.demand.average`, `cpu.usage.average`; `disk.deviceLatency.average`,
`disk.kernelLatency.average`, `disk.queueLatency.average`,
`disk.numberReadAveraged.average`, `disk.numberWriteAveraged.average`,
`disk.commandsAborted.summation`, `disk.busResets.summation`;
`datastore.totalReadLatency.average`, `datastore.totalWriteLatency.average`.
Ready time is reported as a percentage per vCPU, not raw milliseconds.
vCenter keeps 20-second samples for about an hour and coarser rollups
after that; for older windows the checks use vROps and say so.

### 6.4 vROps

For the long-lived things (hosts, clusters, datastores); a 30-minute VM
barely registers.

| Tool | Answers |
| --- | --- |
| `vrops_get_stats(resource, stat_keys, since, until)` | days or weeks of a host's, cluster's or datastore's counters |
| `vrops_compare_window(resource, window, baseline_days)` | the incident window against the same window on previous days: spike, or normal for this cluster? |
| `vrops_get_alerts(resource, since)` | alerts and symptoms on it and its parents |

### 6.5 PowerFlex (optional)

vCenter sees PowerFlex only as a slow device. Which pool or storage node
was saturated, whether a rebuild or rebalance was running, and which
volumes drove the IOPS is visible only from PowerFlex's REST API (gateway
or PowerFlex Manager; endpoints confirmed on your version). Read-only:

| Tool | Answers |
| --- | --- |
| `powerflex_map_datastore(ds)` | the volume, storage pool, protection domain and storage nodes behind a datastore |
| `powerflex_get_stats(object, since)` | IOPS, bandwidth and latency of a volume, pool or node |
| `powerflex_get_activity(since)` | rebuilds, rebalances, degraded or failed devices in the window |
| `powerflex_top_volumes(pool, since)` | the volumes that drove the IOPS on a pool: the noisy neighbour |

Without it, the storage check stops at "datastore latency high" and says
the PowerFlex side was not checked.

## 7. Output shapes, for GLM 5.3

The model reading these results is not a frontier model; the server
carries more of the reasoning:

- **Composite first.** The skill starts every investigation with
  `diagnose_vm` or `diagnose_environment`; the pieces are for drilling in.
- **Findings first, raw values after**, so a model that reads only the
  first lines still gets the answer.
- **Missing data said explicitly**: "no events in window", "counters not
  kept at this statistics level", "PowerFlex not configured", "VM
  destroyed; diagnosis from events and host counters only".
- **Times in UTC, with the clock named.** Sahara, Sims, vCenter, ESXi,
  vROps and PowerFlex keep their own clocks.
- **No vision needed**: the screenshot also comes back as text.
- **Bounded**, the way the Sahara MCP bounds its payloads.

## 8. The skill: `vm-incident`

1. **The ladder**: Sahara Tools error (vCenter, machine, env id, time) →
   `diagnose_vm` → if the rest of the environment is affected,
   `diagnose_environment` → if many environments failed in the same
   window, `diagnose_window` → vROps for the history of the hosts or
   datastores named → PowerFlex if storage was named → Sims logs for what
   Sims did and how long it waited → verdict.
2. **The cause is shared until shown otherwise.** Check the host and the
   storage before explaining the guest; check the environment's healthy
   VMs before blaming the host or datastore they share.
3. **Never identify by name** outside the environment folder; carry the
   key from the first call to the last.
4. **The causes and their evidence**:

   | Cause | Evidence for | Evidence against |
   | --- | --- | --- |
   | ESXi CPU overcommit | affected VMs on hosts above 100% demand; high ready time during boot; CPU busy, console changing | hosts below capacity; ready time low |
   | PowerFlex saturation | affected VMs share datastores on one pool; device latency and pool IOPS high in the boot window; a rebuild or a noisy volume | same pool, same window, healthy VMs booted |
   | Other storage trouble (APD/PDL, paths) | `vmkernel` path errors in the window | none |
   | Datastore full | free space near 0; a pending question about disk space | space healthy |
   | Pending VM question | `runtime.question` set | none |
   | Guest hang in early boot | CPU near zero; console black and frozen across captures; `vmware.log` reset then nothing from the guest; host and storage healthy | console changing; Tools came up |
   | Guest booted, Tools did not start | console at a login prompt or guest IPs reported; Tools not running; host and storage healthy | Tools running |
   | Something else reset or moved it | HA, migration or reset events not from Sims | none |

5. **Starved is not hung.** A VM still booting on an overcommitted host
   is a timeout in Sims or Sahara, not a broken VM; the verdict says
   which.
6. **Correlation rules**: a shared timestamp is not a cause; name the
   evidence for each claim, the competing explanation, and the check that
   separates them.
7. **Evals that bait the failures**: looking up the machine by name
   across vCenters and finding another environment's VM; blaming the
   guest while its host sits at 120%; blaming the host while the
   environment's VMs on other hosts are equally stuck; calling a slowly
   booting VM hung; trusting one black screenshot without a second.

## 9. Security

- **Read-only accounts, one per vCenter**, with a custom role: read
  inventory, console screen read, datastore browse and file read,
  diagnostics (host logs). No other privilege. The exact privilege per
  tool, and that the console route needs nothing that writes, are
  confirmed in the lab.
- **The same for vROps and PowerFlex**: read-only API users.
- **TLS verified** against your internal CA, never turned off.
- **Credentials only in the server's environment**, never in tool
  arguments or results; `.vmx` contents and logs redacted (guestinfo can
  carry secrets).
- **Load**: one session per vCenter, a fixed list of properties per call,
  a concurrency limit per vCenter, a few seconds of caching.
- **Audit log** of every call.

## 10. Phases

| Phase | Builds | Done when |
| --- | --- | --- |
| **0. Collect** (days) | read-only `govc` runs against an affected environment during a real incident, plus the logs of the two past ones | the thresholds and the `vmware.log` / `vmkernel` lines of a starved and a hung boot are on file |
| **1. Lookup + `diagnose_vm`** | 6.1, 6.2 (`diagnose_vm`, `diagnose_environment`), 6.3 | a Sahara Tools error taken to the right machine and a correct finding, on the next live incident |
| **2. vROps + PowerFlex + `diagnose_window`** | 6.4, 6.5, the fleet view | the CPU incident and the PowerFlex incident each named, including for windows older than an hour |
| **3. Skill, full** | section 8 with evals | evals pass with GLM 5.3 in your client |

## 11. Open questions

1. **The env folder's path**: is it the same pattern on all nine vCenters
   (for example `<datacenter>/vm/projects/<env_id>`), or does it vary per
   vCenter or project?
2. **The Sahara log's fields**: the exact keys in the extra data for the
   vCenter, the machine name and the env id, and whether the vCenter is a
   hostname or a short name to map to one.
3. **vCenter and vROps versions**, the statistics level, and the event
   retention setting.
4. **The two past incidents**: dates, windows, the hosts at ~120%, the
   PowerFlex pool. They tune the thresholds and become the first test
   cases.
5. **PowerFlex**: version, gateway or PowerFlex Manager, a read-only API
   user, and whether vROps already has a PowerFlex management pack.
6. **How long Sims and Sahara wait for Tools after a reboot**: the point
   where starved becomes an error.
7. **Does your GLM 5.3 client pass image content** from an MCP result to
   the model? *Default: no; the text form of the screenshot carries it.*
8. **Will the bare metal team grant the read-only accounts?**
