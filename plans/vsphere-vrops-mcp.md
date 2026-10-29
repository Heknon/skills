# Plan: vSphere and vROps for incident investigation (an MCP and a skill)

Status: proposal. Nothing is built. Section 11 lists the questions whose
answers change the design; the recommended answers are the defaults.

## 1. What it is

Today an agent investigating a broken Sahara environment can read two of
the four layers: Sahara (the Sahara MCP: cycles, tests, failures, logs,
live worker state, monitors) and Sims/Twix (their logs in Elastic). When
the trail reaches the virtual machine itself, a person takes over: they
find which of the nine vCenters holds the VM, open the vSphere client,
look at the console, browse the datastore for `vmware.log`, and check
the host and the datastore for latency. This plan puts those last steps
in the agent's reach:

- **`vsphere-mcp`**: a read-only MCP server over all nine vCenters and
  vROps. It finds a VM from any identifier the upper layers hold, and
  answers "what is this VM doing and why" with the console screenshot,
  runtime and guest state, events and tasks, `vmware.log`, the host's
  logs, and the CPU, memory and storage counters around the incident.
- **`vm-incident` skill**: the investigation procedure that spans all
  four layers (Sahara → Sims/Twix → vCenter → vROps), with the causes of
  a stuck VM and the evidence that tells them apart. It ends in a
  verdict, like the other skills here.

The MCP gives access; the skill gives judgement. Either alone is weaker:
an MCP with no procedure leaves the model calling forty tools in a
random order; a skill with no MCP leaves it composing shell commands
against nine endpoints with credentials it should never see.

## 2. The incident it is built around

The one that motivated it, as the agent would work it once this exists:

1. **Sahara**: tests in an environment fail with VMware Tools errors
   after a reboot step. `summarize_failures`, `get_test_failure` give
   the env id, the hostnames and IPs, and the time of the reboot.
2. **Sims/Twix logs**: the environment's VMs and when Sims asked for
   the reboot; Sims' own view of the VM (its name, moref, the vCenter).
3. **vCenter** (new): `find_vm` across the nine. `vm_triage` returns, in
   one call: powered on; Tools `toolsNotRunning`, heartbeat gray since
   the reboot; no pending VM question; console screenshot 99.7% black,
   unchanged across two captures 10 s apart; last `vmware.log` lines show
   the guest reset and the firmware handing over, then nothing from the
   guest; the datastore's write latency peaked at 180 ms for 6 minutes
   across the reboot; three other VMs on the same datastore rebooted in
   the same window.
4. **vROps** (new): the datastore's latency and the host's history over
   the week: does this happen every night at this time?
5. **Verdict** (from the skill): the guest hung early in boot under
   storage latency on datastore X, shared with N other environments;
   evidence for and against; the next check that separates "storage
   latency" from "guest bootloader/kernel problem" (the same image booting
   fine on another datastore).

Steps 3 and 4 are what a person does by hand today, and they take the
most time.

## 3. The layers and how they join

| Layer | Owner | Agent access today | Holds |
| --- | --- | --- | --- |
| Sahara | application | Sahara MCP | cycles, tests, failures, worker identity (`server_id`, host, IP), env id in logs |
| Sims / Twix | infrastructure | logs in Elastic | env → VMs, requests to the VC, its errors |
| vCenter ×9 | bare metal | **none** | VM runtime, guest, console, events, tasks, datastore files, host logs, 20 s counters for the last hour |
| vROps | bare metal | **none** | long history of the same counters, alerts, symptoms, relationships VM → host → cluster → datastore |

The join is the hard part. The MCP must accept whatever the upper layers
give it and find the VM:

| Identifier | Where it comes from | vSphere lookup |
| --- | --- | --- |
| VM name | Sims, Sahara host names | `PropertyCollector` over a `ContainerView` of `VirtualMachine` |
| IP address | Sahara traces, worker identity | `SearchIndex.FindAllByIp(vmSearch=True)` (needs Tools to have reported it once) |
| DNS name | Sahara host names | `SearchIndex.FindAllByDnsName` |
| BIOS or instance UUID | Sims, the guest's DMI | `SearchIndex.FindAllByUuid` |
| moref (`vm-1234`) | Sims | direct, but only meaningful with the vCenter it belongs to |
| Sims env id | Sims | only if Sims stamps it on the VM (tag, custom attribute, annotation, folder, or name pattern): **question 1 in section 11** |

`find_vm` fans out to all nine vCenters in parallel and returns every
match with its vCenter, so a name reused across vCenters is reported as
ambiguous instead of the first hit being trusted. A short-lived index
(VM name/UUID → vCenter, refreshed every few minutes) keeps the fan-out
off the hot path.

## 4. The options

| Option | What it is | For | Against |
| --- | --- | --- | --- |
| **A. Skill + `govc`** | a skill whose recipes run `govc` (one static Go binary, easy to bring into the air gap) with `GOVC_URL` per vCenter | can be in use in days; no service to run; `govc` already has `vm.info`, `events`, `vm.console -capture`, `datastore.download`, `logs`, `metric.sample`, `vm.question` | the model holds credentials in its environment; nine endpoints to iterate by hand; raw JSON floods the context; no enforcement of read-only; screenshots are files the model may not be able to look at |
| **B. MCP only** | typed tools over pyVmomi and the vROps REST API | credentials stay in the server; read-only enforced; fan-out and joining done once, correctly; output bounded and summarised | no procedure: the model still has to know a pending VM question is the first thing to check |
| **C. Both (recommended)** | the MCP for access, the skill for the procedure across Sahara, Sims, vCenter and vROps | each does what it is good at; the skill also covers the Sahara and Elastic steps the MCP cannot | two things to maintain |
| D. Adopt a community server | `vcenter-mcp`, `vSphere-MCP-Pro`, `mcvsphere`, `vcf-ops-mcp` | exist | aimed at VM lifecycle (create, power, snapshot) and inventory, not forensics; single-vCenter; none does screenshot analysis, `vmware.log` reads or host log windows; some connect with TLS verification off |

**Recommendation: C, built in the Sahara MCP's own style** (same package
layout, `pydantic-settings` config, stdio and Streamable HTTP, byte
budgets, concurrency limit, writes off by default). Start with **A as
phase 0** to prove the value on real incidents before the server exists,
and keep it as the fallback when the MCP is down. Community servers are
worth reading for pyVmomi patterns, not worth deploying.

## 5. The MCP's tools

Read-only unless marked. Every tool takes `vcenter` optionally; when it
is missing the server resolves it through `find_vm`. Every result names
the vCenter, the moref, and the time it was read, because a VM's state
an hour ago is not its state now.

### 5.1 Finding things

| Tool | Answers | API |
| --- | --- | --- |
| `list_vcenters` | which vCenters are configured, reachable, their version | `ServiceInstance.content.about` |
| `find_vm(query)` | which VM(s) match a name, IP, DNS name, UUID or moref, on which vCenter | `SearchIndex`, `PropertyCollector` |
| `find_vms_by_env(env_id)` | every VM of a Sims environment | depends on question 1 |
| `get_vm_placement(vm)` | host, cluster, datastores, resource pool, network | `runtime.host`, `datastore`, `resourcePool` |

### 5.2 One VM, now

| Tool | Answers | API |
| --- | --- | --- |
| **`vm_triage(vm)`** | the composite: everything below that is cheap, summarised, with the anomalies listed first | all of the below |
| `get_vm_state(vm)` | power state, connection state, **pending question**, consolidation needed, snapshot chain depth, boot time, uptime, firmware (BIOS/EFI), boot options | `runtime`, `config`, `snapshot` |
| `get_vm_guest(vm)` | Tools running status, version status, heartbeat colour, guest state, IPs, guest OS | `guest`, `guestHeartbeatStatus` |
| `get_vm_console(vm, captures=2, interval_s=10)` | the console as an image, plus text the model can use without vision: fraction of near-black pixels, whether the frame changed between captures, OCR text when an OCR engine is installed | `CreateScreenshot_Task` or the `/screen?id=` endpoint |
| `get_vm_events(vm, since, until)` | power, reset, migration, HA restart, reconfigure, Tools and guest events, error messages | `EventManager.QueryEvents` with an entity filter |
| `get_vm_tasks(vm, since)` | tasks against the VM (who, what, result), including Sims' own | `TaskManager.CreateCollectorForTasks` |
| `get_vm_alarms(vm)` | triggered alarms on the VM, its host, its datastores | `triggeredAlarmState` |

### 5.3 Files and logs

| Tool | Answers | API |
| --- | --- | --- |
| `list_vm_files(vm)` | the VM folder: `vmware*.log`, `.vmx`, `.nvram`, swap, snapshots, sizes and times | `HostDatastoreBrowser.SearchDatastore_Task` |
| `read_vm_log(vm, which=0, tail, grep, since)` | lines of `vmware.log` (or `vmware-N.log`, the rotated ones from before the reboot), filtered server side | HTTPS `GET /folder/<path>?dcPath=&dsName=` |
| `read_vmx(vm)` | the `.vmx`, secrets redacted | same |
| `read_host_log(host, log, since, grep)` | `vmkernel`, `hostd`, `vpxa` lines around the incident: storage path failures, APD/PDL, latency warnings, NFS/iSCSI resets | `DiagnosticManager.BrowseDiagnosticLog` |

`read_vm_log` and `read_host_log` never return the whole file: a
`tail` / `grep` / time window is required, results are capped by
`VSPHERE_MAX_LOG_LINES`, and the default `grep` is a curated list of
lines that matter in a boot hang (VM questions, stuns, resets, storage
errors, Tools state changes, firmware messages). The list is built from
your own logs in the lab, not from memory (section 9).

### 5.4 Contention

| Tool | Answers | API |
| --- | --- | --- |
| `get_vm_metrics(vm, since, until, counters)` | CPU ready and co-stop, memory balloon/swap, per-disk latency and IOPS, network drops | `PerfManager.QueryPerf` (20 s realtime for about an hour; coarser after, depending on the statistics level) |
| `get_host_metrics(host, ...)` | the host: CPU, memory, device and kernel latency per datastore | same |
| `get_datastore_health(datastore)` | free space (a thin VM on a full datastore pauses with a question), accessibility, latency, how many VMs and from which environments | `summary`, `PerfManager` |
| **`find_neighbours(vm, since, until)`** | the other VMs on the same host and datastores, and which of them also rebooted, failed Tools, or saw latency in the window: "is it this VM or the infrastructure?" | events + metrics across the placement |

### 5.5 vROps

| Tool | Answers | API |
| --- | --- | --- |
| `vrops_find_resource(name, kind)` | the vROps resource for a VM, host, datastore, cluster | `GET /suite-api/api/resources?name=&resourceKind=` |
| `vrops_get_stats(resource, stat_keys, since, until, rollup)` | days or weeks of the same counters, at 5 minutes | `GET /suite-api/api/resources/{id}/stats` |
| `vrops_get_alerts(resource, since)` | alerts and their symptoms, on the resource and its parents | `/api/alerts`, `/api/symptoms` |
| `vrops_get_relationships(resource)` | VM → host → cluster → datastore as vROps sees them | `/api/resources/{id}/relationships` |
| `vrops_compare_window(resource, incident, baseline)` | the counters in the incident window against the same window on previous days: "is this unusual?" | two `stats` queries, compared server side |

vROps answers what vCenter's realtime counters cannot: anything older
than about an hour, and whether a spike is normal for that time of day.

### 5.6 Actions (off by default)

Behind `VSPHERE_ACTIONS=1`, a separate vCenter role, and a confirmation
the tool asks for explicitly:

| Tool | Does |
| --- | --- |
| `answer_vm_question(vm, question_id, choice)` | answers the pending question that blocks a boot |
| `reset_vm(vm)` / `shutdown_guest(vm)` | the reset a person would do after the evidence is captured |
| `take_console_capture(vm)` | stores a screenshot on the datastore for the record |

Nothing that creates, deletes, migrates or reconfigures. Those belong to
Sims, and an incident agent changing placement behind Sims' back makes
the next incident harder to read.

## 6. Output shapes, for the model you run

The model reading these results is GLM 5.3, not a frontier model, and
the tool design must carry more of the reasoning:

- **Few, composite tools first.** `vm_triage` and `find_neighbours` do
  in one call what would otherwise be eight; the skill tells the model
  to start with them. The fine-grained tools are there to drill into
  one finding.
- **Anomalies first, numbers second.** Every result starts with
  `findings: [...]` (for example, "Tools heartbeat gray for 47 min, since
  the reset at 02:13:05") and ends with the raw values. A model that
  reads only the first lines still gets the answer.
- **Explicit missing data.** "No events in window" and "counters not
  available at this statistics level" are different findings and are
  said so, the way the Sahara MCP marks missing observations.
- **Times in UTC with the source's clock named.** Sahara, Sims, vCenter,
  ESXi hosts and vROps each have their own clock; a correlation across
  them is only as good as the alignment.
- **No vision needed.** The console screenshot comes back as an image
  *and* as text (black fraction, changed or frozen, OCR). Whether GLM
  5.3 in your client accepts image content is question 5.
- **Bounded.** Line, byte, sample and match limits, the same way the
  Sahara MCP bounds its payloads, and a stated truncation when they bite.

## 7. The skill: `vm-incident`

What `SKILL.md` carries, in this repo's style (judgement, a procedure
that ends in a verdict, evals that bait the failures):

1. **The ladder**: Sahara (which tests, which env, when) → Sims/Twix logs
   (which VMs, what Sims asked for, what the VC answered) → `vm_triage`
   → `find_neighbours` → vROps history → verdict. Do not start at the
   bottom: a VM's metrics mean nothing without the time and the symptom
   from the top.
2. **The causes of "VM stuck after reboot"** and what tells them apart:

   | Cause | Evidence for | Evidence against |
   | --- | --- | --- |
   | Pending VM question (moved/copied, disk full, CD-ROM) | `runtime.question` set; VM "running" but no CPU use | no question |
   | Datastore full | free space near 0; question about disk space; the VM paused | free space healthy |
   | Storage latency, APD/PDL | high device/kernel latency in the window; `vmkernel` path errors; neighbours on the same datastore affected | latency normal; neighbours fine |
   | Guest hang in early boot (firmware, bootloader, kernel) | console frozen and black or on a firmware/bootloader screen; `vmware.log` shows the reset and nothing from the guest after; neighbours fine | Tools came up, guest IPs reported |
   | Guest booted, Tools did not start | guest IPs or console login prompt present; Tools `toolsNotRunning`; heartbeat gray | Tools running |
   | Host contention | CPU ready / co-stop high; memory swap/balloon on the host | host quiet |
   | Something moved it | migration, HA restart or reconfigure event in the window; a Sims task at that time | no such event |

3. **Correlation rules**: one spike at the same time is not a cause; name
   the evidence for each claim, the competing explanation, and the next
   check that separates them (the Sahara MCP's `INVESTIGATION.md` sets
   the same bar).
4. **When to stop and hand over**: an action (answer, reset) is a
   person's decision; capture the screenshot and logs first.
5. **Evals that bait the failures**: blaming the VM when the datastore
   is the shared factor; reading `vmware.log` from after the reset only
   and missing the rotated one from before; trusting a VM name found on
   the first vCenter when another vCenter has one too; reading
   "no events" as "nothing happened" when the window was wrong; treating
   a black screenshot as proof of a hang without a second capture.

## 8. Security and operations

- **Service accounts, one per vCenter**, with a custom read-only role:
  read (`System.View`, `System.Read`), console screenshot
  (`VirtualMachine.Interact.CreateScreenshot`), datastore read
  (Browse datastore, Low level file operations), host logs
  (`Global.Diagnostics`). The exact privilege set for each tool is
  confirmed in the lab, on your vCenter version.
- **Actions** use a second account with a second role, only loaded when
  `VSPHERE_ACTIONS=1`.
- **TLS verified** against your internal CA (`VSPHERE_CA_BUNDLE`), never
  turned off.
- **Credentials only in the server's environment**, never in tool
  arguments or results. `.vmx` contents and logs pass through a redaction
  filter (guestinfo variables can carry secrets).
- **Load on the vCenters**: one session per vCenter reused, property
  collection limited to the fields asked for, a concurrency limit per
  vCenter, results cached for seconds. Nine vCenters each with a heavy
  `PropertyCollector` call per question would be noticed by the bare
  metal team before it is useful.
- **Audit log** of every call: who, which VM, which tool. The console
  can show what is on a guest's screen.
- **Where it runs**: next to the Sahara MCP (OpenShift, Streamable HTTP)
  for shared use, or stdio on an investigator's machine. The VC and
  vROps endpoints must be reachable from wherever it runs.

## 9. Things to verify in the lab, before writing them down

On your vCenter and vROps versions, not from documentation memory:

- which screenshot route works through vCenter with your privileges, and
  what a black console returns (an all-black PNG, an error, or nothing);
- the `vmware.log` lines a boot hang, a pending question, a stun and an
  APD actually produce: collect them from past incidents, and build the
  default `grep` list and the skill's evidence table from them;
- which log keys `DiagnosticManager` offers on your ESXi version, and
  how far back they go;
- the vCenter statistics level (it decides what `QueryPerf` has beyond
  the last hour);
- the vROps stat keys for VM, host and datastore latency, ready time,
  balloon and swap, on your version;
- what Sims writes on a VM that names its environment (question 1).

## 10. Phases

| Phase | Builds | Done when |
| --- | --- | --- |
| **0. govc recipes** (days) | the skill's first draft with `govc` recipes per vCenter: find the VM, `vm.info`, `vm.question`, `events`, `vm.console -capture`, `datastore.download` of `vmware.log`, `logs -log vmkernel`, `metric.sample` | two past incidents re-investigated with them, and the time compared with the manual run |
| **1. MCP, read-only, vCenter** | sections 5.1–5.4, `vm_triage` and `find_neighbours` first | the black-screen incident worked end to end through Sahara MCP + Elastic + this |
| **2. vROps** | section 5.5 | "was this unusual" answered from history |
| **3. Skill, full** | section 7, with the evidence table from phase 0 and 1 incidents, and evals | evals pass with GLM 5.3 in your client |
| **4. Actions** (optional) | section 5.6 | the bare metal team agrees to the role |

## 11. Open questions

1. **How does a VM name its Sims environment?** A tag, a custom
   attribute, an annotation, a folder, a naming pattern? This decides
   whether `find_vms_by_env` is one query or a join through Sims logs.
   *Default: read it from Sims logs in Elastic until we know.*
2. **vCenter and vROps versions**, and whether the nine vCenters are in
   Enhanced Linked Mode (one login, one search) or separate. *Default:
   separate, one session each.*
3. **Is anything from vCenter or ESXi already in Elastic** (events,
   syslog from the hosts)? If yes, part of section 5.3 can be a query
   the agent already knows how to run. *Default: no.*
4. **Will the bare metal team grant a read-only service account** with
   console screenshot and datastore read? Everything here starts there.
5. **Which client runs GLM 5.3, and does it pass image content** from an
   MCP result to the model? *Default: no; the text form of the
   screenshot carries the finding.*
6. **Where should it run**: shared on OpenShift beside the Sahara MCP,
   or per investigator over stdio? *Default: beside the Sahara MCP.*
