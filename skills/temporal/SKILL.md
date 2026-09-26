---
name: temporal
description: Develop, debug, and manage Temporal applications in Python with the temporalio SDK. Use when building workflows, activities, workers, or background job queues with Temporal, debugging non-determinism errors, stuck workflows, or activity retries, using the Temporal CLI or dev server, or working with durable execution concepts like signals, queries, updates, heartbeats, versioning, continue-as-new, child workflows, or saga patterns. Also use for "run a Temporal workflow from the CLI", "start a dev server", "temporal server start-dev", "temporal workflow start", "temporal workflow execute", "temporal workflow signal", "temporal workflow query", "temporal workflow update", and for Temporal as a replacement for Celery, RQ, Dramatiq or another job queue.
---

# Skill: temporal (Python)

The Python part of Temporal's official developer skill
([temporalio/skill-temporal-developer](https://github.com/temporalio/skill-temporal-developer),
MIT, see `LICENSE`), kept word for word under `references/`. Only this
file is adapted: other languages are removed and the section below says
how to work air gapped. `UPSTREAM.md` records the commit it came from and
how to update it.

## Working air gapped

- **The SDK comes from the mirror.** Add it with `uv add temporalio`
  (extras such as `temporalio[opentelemetry]` the same way); where a
  reference says `pip install`, use uv. The packaging skill covers the
  mirror and the index settings.
- **The Temporal CLI is a binary, not a Python package.**
  `references/core/install_cli.md` downloads it from temporal.download,
  Homebrew or Snap, none of which the air-gapped side can reach. Check
  `temporal --version` first; if it is missing, say so and ask for the
  binary (or its archive) to be brought across the gap, as the
  packaging skill's across-the-gap procedure does for wheels. Do not try
  the download commands.
- **Links to docs.temporal.io and GitHub will not open.** The facts in
  `references/` are the source; for what the installed SDK really
  accepts, read its code (`uv run python -c "import temporalio;
  print(temporalio.__file__)"`), as the offline-docs skill teaches.
- **Read the SDK version first**, from `uv.lock` or
  `uv run python -c "from importlib.metadata import version;
  print(version('temporalio'))"`, and treat any reference that names a
  newer feature as something to confirm in the installed code.

## Overview

Temporal is a durable execution platform that makes workflows survive
failures automatically. This skill provides guidance for building
Temporal applications in Python.

## Core Architecture

The **Temporal Cluster** is the central orchestration backend. It maintains three key subsystems: the **Event History** (a durable log of all workflow state), **Task Queues** (which route work to the right workers), and a **Visibility** store (for searching and listing workflows). There are three ways to run a Cluster:

- **Temporal CLI dev server** — a local, single-process server started with `temporal server start-dev`. Suitable for development and testing only, not production.
- **Self-hosted** — you deploy and manage the Temporal server and its dependencies (e.g., database) in your own infrastructure for production use.
- **Temporal Cloud** — a fully managed production service operated by Temporal. No cluster infrastructure to manage.

**Workers** are long-running processes that you run and manage. They poll Task Queues for work and execute your code. You might run a single Worker process on one machine during development, or run many Worker processes across a large fleet of machines in production. Each Worker hosts two types of code:

- **Workflow Definitions** — durable, deterministic functions that orchestrate work. These must not have side effects.
- **Activity Implementations** — non-deterministic operations (API calls, file I/O, etc.) that can fail and be retried.

Workers communicate with the Cluster via a poll/complete loop: they poll a Task Queue for tasks, execute the corresponding Workflow or Activity code, and report results back.

## History Replay: Why Determinism Matters

Temporal achieves durability through **history replay**:

1. **Initial Execution** - Worker runs workflow, generates Commands, stored as Events in history
2. **Recovery** - On restart/failure, Worker re-executes workflow from beginning
3. **Matching** - SDK compares generated Commands against stored Events
4. **Restoration** - Uses stored Activity results instead of re-executing

**If Commands don't match Events = Non-determinism Error = Workflow blocked**

| Workflow Code | Command | Event |
| -- | -- | -- |
| Execute activity | `ScheduleActivityTask` | `ActivityTaskScheduled` |
| Sleep/timer | `StartTimer` | `TimerStarted` |
| Child workflow | `StartChildWorkflowExecution` | `ChildWorkflowExecutionStarted` |

See [Temporal determinism rules](references/core/determinism.md) for detailed explanation.

## Getting Started

### Ensure Temporal CLI is installed

Check if `temporal` CLI is installed (`temporal --version`). If not, see
"Working air gapped" above before [Temporal CLI installation guide](references/core/install_cli.md).

### Read All Relevant References

1. First, read the [Python SDK guide](references/python/python.md).
2. Second, read appropriate `core` and Python-specific references for the task at hand.

## Primary References

- **[Temporal determinism rules](references/core/determinism.md)** - Why determinism matters, replay mechanics, basic concepts of activities
  - Python: [determinism](references/python/determinism.md), [determinism protection (the sandbox)](references/python/determinism-protection.md)
- **[Temporal workflow patterns](references/core/patterns.md)** - Conceptual patterns (signals, queries, saga)
  - Python: [patterns](references/python/patterns.md)
- **[Temporal common pitfalls](references/core/gotchas.md)** - Anti-patterns and common mistakes
  - Python: [gotchas](references/python/gotchas.md)
- **[Temporal versioning guide](references/core/versioning.md)** - Versioning strategies and concepts - how to safely change workflow code while workflows are running
  - Python: [versioning](references/python/versioning.md)
- **[Temporal standalone Activities guide](references/core/standalone-activities.md)** - Standalone Activities: run an Activity directly from a Client without a Workflow — Temporal's job queue
  - Python: [standalone activities](references/python/standalone-activities.md)
- **[Temporal Task Queue priority and fairness guide](references/core/priority-fairness.md)** - Task Queue Priority and Fairness concepts, configuration, and limitations
  - Python: [priority and fairness](references/python/priority-fairness.md)
- **[Temporal troubleshooting guide](references/core/troubleshooting.md)** - Decision trees, recovery procedures
- **[Temporal error reference](references/core/error-reference.md)** - Common error types, workflow status reference
  - Python: [error handling](references/python/error-handling.md)
- **[Temporal interactive workflow guide](references/core/interactive-workflows.md)** - Testing signals, updates, queries
- **[Temporal development management guide](references/core/dev-management.md)** - Dev cycle & management of server and workers
- **[Temporal CLI workflow command guide](references/core/cli-workflow-commands.md)** - Developer-facing CLI commands for workflow interaction (start, execute, signal, query, update)
- **[Temporal AI integration patterns](references/core/ai-patterns.md)** - AI/LLM pattern concepts
  - Python: [AI patterns](references/python/ai-patterns.md)

## Python-specific topics

- **[Sync vs async](references/python/sync-vs-async.md)** - choosing sync or async activities and the executors they need
- **[Testing](references/python/testing.md)** - the time-skipping test environment, replay tests, mocking activities
- **[Data handling](references/python/data-handling.md)** - data converters, payload codecs, pydantic
- **[External storage](references/python/external-storage.md)** - large payloads kept outside history
- **[Workflow streams](references/python/workflow-streams.md)** - streaming progress out of a running workflow
- **[Observability](references/python/observability.md)** - logging, metrics, tracing
- **[Advanced features](references/python/advanced-features.md)** - schedules, async activity completion, sandbox customization, worker tuning, `@workflow.init`, failure exception types

## Job Queues and Background Jobs

**Temporal's job queue is Standalone Activities.** When the developer asks for a job queue, background or async jobs, a work queue, or whether Temporal can replace Celery, Sidekiq, BullMQ, Resque, Hangfire, or SQS-plus-workers, build it with a Standalone Activity — not a Workflow wrapping a single Activity, and not a dispatcher Workflow that receives jobs by Signal.

Temporal **Task Queues** are the routing mechanism Workers poll, not a queue that producers push jobs into. Do not answer a job queue question by describing Temporal Task Queues.

When a developer says "task queue" they may mean "job queue": Celery, Dramatiq, Huey, and Asynq all use Task nomenclature, while Sidekiq, Hangfire, BullMQ, Resque, RQ, and Faktory use Job. Read "can I use Temporal as a task queue?" as a job queue question, and reserve Temporal's Task Queue meaning for your own reply.

- **[Temporal job queue guide](references/core/job-queue.md)** - Job-queue vocabulary mapped to Temporal, migrating off an existing job queue, anti-patterns, and per-language SDK guides and runnable samples

## Third-Party Integrations

For Temporal plugins and integrations with third-party Python frameworks and SDKs (OpenAI Agents SDK, Google ADK, LangGraph, Pydantic AI, OpenTelemetry, etc.), see **[integrations catalog](references/integrations.md)**, a table of what each integration does and its reference file under `references/python/integrations/`.

## Feedback

If this skill's explanations are unclear, misleading, or missing
something, say so in your answer and describe what would have helped.
The person can report it upstream at
https://github.com/temporalio/skill-temporal-developer/issues from a
connected machine; do not try to file it yourself.
