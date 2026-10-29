# Plan: vSphere and vROps for incident investigation (an MCP and a skill)

Status: proposal. Nothing is built. Section 12 lists the questions whose
answers change the design; the recommended answers are the defaults.

## 1. What it is

Today an agent investigating a broken Sahara environment can read two of
the four layers: Sahara (the Sahara MCP) and Sims/Twix (their logs in
Elastic). When the trail reaches the VMs, a person takes over: opens the
vCenter, finds the VMs that are stuck, looks at the console, browses the
datastore for `vmware.log`, checks the host and the datastore. This plan
puts those steps in the agent's reach:

- **`vsphere-mcp`**: a read-only MCP server over all nine vCenters and
  vROps. Its main question is **"which VMs across the fleet are in a
  state they should not be in, what do they have in common, and why"**,
  not "tell me about VM X".
- **`vm-incident` skill**: the investigation procedure across all four
  layers, with the causes of a stuck VM and the evidence that separates
  them. It ends in a verdict.

The MCP gives access; the skill gives judgement.

## 2. The fleet it is built for

This is not a classic vSphere estate, and tools built for one get it
wrong:

- **VMs are cattle.** Sims creates them for an environment and destroys
  them after 10 minutes to 24 hours. Hundreds or thousands exist at once,
  spread by load across nine vCenters.
- **A name is a label, not an identity.** The same name is reused by the
  next environment an hour later, possibly on another vCenter. "VM
  `x-web-01`" means nothing without *which one*.
- **Per-VM history barely exists.** A 30-minute VM has no week of metrics
  to compare against. The baseline is **the population**: the other VMs
  created from the same template, at the same time, on the same host or
  datastore.
- **Evidence is destroyed with the VM.** `vmware.log` lives in the VM's
  folder on the datastore; when Sims deletes the VM, the log goes with it.
  The console, the guest state and the realtime counters go too. What
  survives: vCenter's events and tasks (in its database, for its
  retention period), vROps' data on the host, datastore and cluster, and
  Sims' logs in Elastic.

Three consequences shape everything below:

1. **Identity is `(vcenter, moref)`**, with `instanceUuid` and
   `config.createDate` alongside. The name is shown, never looked up by.
   A follow-up call on a key that no longer exists says *destroyed* and
   never falls back to another VM with the same name.
2. **The entry point is a sweep**, not a lookup: every VM on every
   vCenter, classified by how wrong its state is, then grouped by what
   the wrong ones share.
3. **Capture before it is gone**: an anomalous VM's logs, screenshot and
   state are copied out while it still exists (section 6).

## 3. The incident it is built around

1. **Sahara**: tests fail with VMware Tools errors after a reboot step,
   across several environments.
2. **`sweep_vms`** across nine vCenters: 41 of 1,870 VMs are anomalous;
   33 are "powered on, booted more than 10 minutes ago, Tools never came
   up, CPU near zero". Grouped: 29 of the 33 are on datastore `ds-17`,
   which holds 210 VMs; the other 177 on it are fine, but all 29 rebooted
   between 02:10 and 02:16; VMs created from the same template on other
   datastores booted normally.
3. **`vm_triage`** on three of them, chosen by the sweep as
   representatives: console black and frozen across two captures;
   `vmware.log` shows the reset and the firmware, then nothing from the
   guest; no pending question.
4. **`read_host_log`** and **`get_datastore_health`**: device latency on
   `ds-17` above 150 ms from 02:09 to 02:17 on four hosts; `vmkernel`
   path warnings in the same window. **vROps**: `ds-17` latency spikes
   every night near 02:10 this week.
5. **Verdict** (from the skill): VMs that rebooted during a nightly
   latency spike on `ds-17` hung in early boot; the VM and the template
   are not the cause, because the same template booted fine elsewhere and
   the rest of `ds-17` was fine outside the reboot window. Next check:
   what runs against `ds-17` at 02:10.

The grouping in step 2 is the finding. One stuck VM is an anecdote;
29 of 33 on one datastore inside six minutes is a cause to chase.

## 4. The layers and how they join

| Layer | Owner | Agent access today | Holds |
| --- | --- | --- | --- |
| Sahara | application | Sahara MCP | cycles, tests, failures, worker host/IP, env id in logs, the time of each step |
| Sims / Twix | infrastructure | logs in Elastic | env → VMs (with the vCenter and moref, if it logs them), what it asked the VC, when it destroyed what |
| vCenter ×9 | bare metal | **none** | live VM state, console, `vmware.log` while the VM exists; events and tasks after it is gone; 20 s counters for about the last hour |
| vROps | bare metal | **none** | history of hosts, datastores and clusters; alerts. Short-lived VMs barely register. |

The join from the upper layers is **env id + time window**, never a name:

| From | To the VM | Holds after the VM is destroyed? |
| --- | --- | --- |
| Sims log line with vCenter + moref | direct | yes, as a key into events |
| Sims log line with name + creation time | name, `createDate` within the window, same vCenter | yes, through events |
| Sahara worker IP + time | `guest.ipAddress` on a live VM | no: IPs are reused too |
| An env marker on the VM (tag, custom attribute, annotation, folder) | query by marker | only while the VM lives (question 1) |

## 5. The options

| Option | What it is | For | Against |
| --- | --- | --- | --- |
| **A. Skill + `govc`** | a skill whose recipes run `govc` (one static Go binary) per vCenter | in use within days | a fleet sweep is nine big JSON dumps for the model to read; no grouping; credentials sit in the model's environment; no read-only guarantee |
| B. MCP only | typed tools over pyVmomi and the vROps REST API | the sweep, grouping and capture done once and correctly, on the server | no procedure for reading what it finds |
| **C. Both (recommended)** | the MCP for access, sweeping and capture; the skill for the procedure | each does what it is good at | two things to maintain |
| D. Adopt a community server | `vcenter-mcp`, `vSphere-MCP-Pro`, `mcvsphere`, `vcf-ops-mcp` | they exist | built around one named VM on one vCenter, for lifecycle and inventory: the opposite of this fleet |

**Recommendation: C, built in the Sahara MCP's style** (package layout,
`pydantic-settings` config, stdio and Streamable HTTP, byte budgets,
concurrency limit, writes off by default). `govc` as phase 0 to collect
real examples of stuck VMs before the server exists.

## 6. The MCP's tools

Read-only unless marked. Every result names the vCenter, the moref, the
`instanceUuid`, the creation time and the time it was read. Follow-up
tools take that key, never a name.

### 6.1 The sweep: the entry point

| Tool | Answers |
| --- | --- |
| **`sweep_vms(vcenters=all, since, classes=all)`** | every VM in every vCenter, classified; returns the anomalous ones with their class, and the **groupings**: by vCenter, cluster, host, datastore, template or image, creation-time bucket, boot-time bucket. Each group is shown against its population ("29 of 210 on `ds-17`; fleet rate 2%") |
| `explain_group(sweep_id, group)` | what the members of one group share and what the healthy rest of its population does not: host, datastore, template, the minute they booted, the events before it |
| `sweep_history(since, until)` | the same classes for VMs that are **already destroyed**, from vCenter events and tasks: resets, failed power-ons, HA resets, Tools never running before the destroy |

One `PropertyCollector` call per vCenter over a `ContainerView`, asking
only for the fields the classes need: `runtime.powerState`,
`runtime.connectionState`, `runtime.bootTime`, `runtime.question`,
`runtime.consolidationNeeded`, `guest.toolsRunningStatus`,
`guestHeartbeatStatus`, `guest.ipAddress`, `summary.quickStats`
(CPU usage, uptime), `config.createDate`, `config.instanceUuid`,
`runtime.host`, `datastore`, and whatever Sims marks the env and template
with. That is cheap enough to run every minute across nine vCenters;
pulling full VM objects is not.

The anomaly classes, with thresholds in config:

| Class | Rule |
| --- | --- |
| `stuck_after_boot` | powered on, booted more than N minutes ago, Tools not running, heartbeat gray |
| `blocked_on_question` | `runtime.question` set |
| `hung` | stuck after boot and CPU near zero |
| `spinning` | stuck after boot and CPU pinned at one or more full vCPUs (boot loop, panic loop) |
| `boot_loop` | more than K resets or guest reboots in the window, from events |
| `lost_heartbeat` | Tools were running, heartbeat now red or gray |
| `unexpected_off` | powered off, not by a Sims task, within its environment's life |
| `inaccessible` | connection state disconnected, inaccessible, orphaned or invalid |
| `needs_consolidation` | `consolidationNeeded` set |
| `leaked` | older than the longest environment lifetime (24 h) |

The classes and thresholds are a first guess; phase 0 tunes them against
VMs a person has already judged.

### 6.2 One VM, while it lives

| Tool | Answers | API |
| --- | --- | --- |
| **`vm_triage(key)`** | the composite: state, guest, console, recent events, the relevant `vmware.log` lines, neighbours; anomalies listed first | all below |
| `get_vm_console(key, captures=2, interval_s=10)` | the console as an image, plus text for a model without vision: black fraction, frozen or changing between captures, OCR when an engine is installed | `CreateScreenshot_Task` or `/screen?id=` |
| `get_vm_events(key, since)` | power, reset, migration, HA, reconfigure, Tools and guest events; works for destroyed VMs too | `EventManager.QueryEvents` |
| `get_vm_tasks(key, since)` | tasks against it, Sims' included | `TaskManager` collectors |
| `read_vm_log(key, which=0, grep, tail, since)` | `vmware.log` and the rotated `vmware-N.log` from before the reboot, filtered on the server | HTTPS `GET /folder/<path>?dcPath=&dsName=` |
| `get_vm_metrics(key, counters)` | CPU ready and co-stop, balloon/swap, disk latency, for its short life | `PerfManager.QueryPerf` (20 s realtime) |

### 6.3 Capture: before Sims destroys it

| Tool | Does |
| --- | --- |
| **`capture_vm_evidence(key)`** | copies the state, two screenshots, `vmware*.log`, the `.vmx` (redacted), the last hour of events and counters, and the host's log window into an evidence store outside vSphere; returns a capture id |
| `get_capture(id)` / `list_captures(env, since)` | reads them back, after the VM is gone |

The agent calls it when it finds something; the **sweeper** (section 8)
calls it for every new anomaly, so evidence exists for the incident
nobody was watching. The better answer is for Sims to call it before it
destroys an anomalous VM, or to hold such VMs for a short while instead
of destroying them (question 3).

### 6.4 The shared infrastructure

| Tool | Answers | API |
| --- | --- | --- |
| `get_datastore_health(ds, since)` | free space, accessibility, latency over the window, how many VMs live on it and how many are anomalous | `summary`, `PerfManager` |
| `get_host_health(host, since)` | CPU, memory, per-datastore device and kernel latency, anomalous VMs on it | same |
| `read_host_log(host, log, since, grep)` | `vmkernel`, `hostd` lines in the window: path failures, APD/PDL, latency warnings | `DiagnosticManager.BrowseDiagnosticLog` |

### 6.5 vROps

vROps matters here for the **long-lived things**: hosts, datastores,
clusters, and the vCenters themselves. A VM that lived 30 minutes is a
few points at best and may already be gone from it.

| Tool | Answers |
| --- | --- |
| `vrops_get_stats(resource, stat_keys, since, until)` | days or weeks of a host's, datastore's or cluster's counters |
| `vrops_compare_window(resource, window, baseline_days)` | the incident window against the same window on previous days: "is 02:10 always like this?" |
| `vrops_get_alerts(resource, since)` | alerts and symptoms on it and its parents |

### 6.6 Actions (off by default)

Behind `VSPHERE_ACTIONS=1`, a second vCenter role, and an explicit
confirmation: `answer_vm_question`, `reset_vm`. Nothing that creates,
deletes, migrates or reconfigures: that is Sims' job, and an agent doing
it behind Sims makes the next incident harder to read. Evidence is
captured before any action.

## 7. Output shapes, for GLM 5.3

The model reading these results is not a frontier model; the server
carries more of the reasoning:

- **The sweep summarises; it does not dump.** Counts, classes and the top
  groupings against their population first; the member list paged after.
  Two thousand VM rows in the context is a failure.
- **Representatives, not everyone.** A group comes with two or three
  members chosen to triage (the earliest, the most typical), so the model
  does not triage 33 VMs one by one.
- **Findings first, raw values after**, and missing data said
  explicitly: "no events in window" is not "nothing happened".
- **Times in UTC, with the clock named.** Sahara, Sims, vCenter, ESXi
  and vROps keep their own clocks.
- **No vision needed.** The screenshot also comes back as text.
- **Bounded**, the way the Sahara MCP bounds its payloads.

## 8. The sweeper

The MCP answers questions; a small service beside it **records**. Every
minute it runs the sweep, writes each anomalous VM (key, class, placement,
env marker, times) to Elastic, and calls `capture_vm_evidence` on new
ones. Then:

- an incident from last night is still investigable this morning, after
  the VMs are gone;
- "how many `stuck_after_boot` per hour, per datastore, this month" is an
  Elastic query, the same kind the agent already runs against Sims logs;
- the anomaly rate per datastore or host is a population baseline that
  vROps cannot give for VMs this short-lived.

It runs the same code as `sweep_vms`, so the classes stay in one place.

## 9. The skill: `vm-incident`

What `SKILL.md` carries, in this repo's style:

1. **The ladder**: Sahara (which tests, which envs, when) → Sims logs
   (which VMs, which vCenters, what Sims did) → `sweep_vms` or
   `sweep_history` for that window → `explain_group` → `vm_triage` on the
   representatives (or their captures) → shared infrastructure → vROps
   history → verdict.
2. **Population before individual.** Before explaining one VM, find how
   many are like it and what they share; before blaming what they share,
   check that its healthy members were not in the same situation.
3. **Never identify by name.** Carry the key from the first tool to the
   last; a name match across time or vCenters is a different VM.
4. **The causes and their evidence**:

   | Cause | Evidence for | Evidence against |
   | --- | --- | --- |
   | Storage latency, APD/PDL | the group shares a datastore; latency and `vmkernel` errors in its boot window | same datastore, same window, healthy VMs booted |
   | Datastore full | free space near 0; `blocked_on_question` about disk space | space healthy |
   | Host contention | the group shares a host; ready time, swap or balloon high | spread across hosts |
   | Bad template or image | the group shares a template across datastores and hosts | the template boots fine elsewhere |
   | Guest hang in early boot | console black and frozen; `vmware.log` reset then nothing from the guest | Tools came up |
   | Guest booted, Tools did not start | console at a login prompt or guest IP reported; Tools not running | Tools running |
   | Pending question | `runtime.question` set | none |
   | Something moved or reset it | HA, migration or reconfigure events in the window, not from Sims | none |
   | vCenter itself | anomalies on one vCenter only, tasks slow or failing there | spread across vCenters |

5. **Correlation rules**: a shared timestamp is not a cause; name the
   evidence for each claim, the competing explanation, and the check that
   separates them.
6. **Evals that bait the failures**: following a VM by name into the next
   environment's VM; explaining one VM in detail when 30 share a datastore;
   blaming a datastore without checking its healthy VMs; reading a
   destroyed VM's absence as "no problem"; trusting one black screenshot
   without a second.

## 10. Security and operations

- **Service accounts, one per vCenter**, with a custom read-only role:
  read, console screenshot, datastore browse and file read, diagnostics
  (host logs). The exact privileges per tool are confirmed in the lab.
- **Actions** use a second account and role, loaded only with the flag.
- **TLS verified** against your internal CA, never turned off.
- **Credentials only in the server**, never in arguments or results;
  `.vmx` and logs redacted (guestinfo can carry secrets).
- **Load on the vCenters**: the sweep asks for a fixed list of
  properties, one session per vCenter, a concurrency limit per vCenter.
  The sweeper's once a minute is the load to agree with the bare metal
  team; the agent's sweeps read the sweeper's latest result when it is
  fresh enough.
- **Audit log** of every call.
- **Where it runs**: beside the Sahara MCP, on OpenShift.

## 11. Phases

| Phase | Builds | Done when |
| --- | --- | --- |
| **0. Collect** (days) | `govc` scripts that dump the sweep properties from all nine vCenters, run during a few bad nights; a person labels which VMs were really stuck | the anomaly classes and thresholds are tuned on real data, and the `vmware.log` lines of a real hang are on file |
| **1. Sweep + triage** | 6.1, 6.2, 6.4, read-only | the black-screen incident worked end to end through Sahara MCP + Elastic + this, while the VMs lived |
| **2. Capture + sweeper** | 6.3 and section 8 | last night's incident investigated this morning, after the VMs were destroyed |
| **3. vROps** | 6.5 | "is this window unusual for this datastore" answered |
| **4. Skill, full** | section 9 with evals | evals pass with GLM 5.3 in your client |
| 5. Actions (optional) | 6.6 | the bare metal team agrees to the role |

## 12. Open questions

1. **What does Sims put on a VM?** An env id or template as a tag,
   custom attribute, annotation, folder or name pattern? This decides
   whether the sweep can group by environment and template directly.
   *Default: join through Sims logs in Elastic.*
2. **Do Sims logs carry the vCenter and moref** of each VM it creates and
   destroys? That is the join that survives destruction. *Default: name +
   time, which is weaker.*
3. **Can Sims hold or capture an anomalous VM before destroying it?** A
   hook to `capture_vm_evidence`, or a short hold. Without it, phase 2's
   sweeper is the only capture. *Default: the sweeper.*
4. **vCenter and vROps versions**, and the vCenter event retention
   setting: it decides how far back `sweep_history` reaches.
5. **Is anything from vCenter or ESXi already in Elastic** (events, host
   syslog)? *Default: no.*
6. **Will the bare metal team grant the read-only accounts**, and accept
   a once-a-minute sweep's load on nine vCenters?
7. **Does your GLM 5.3 client pass image content** from an MCP result to
   the model? *Default: no; the text form of the screenshot carries it.*
