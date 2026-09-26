# Third-Party Integrations Catalog

Temporal ships and supports a growing set of integrations with third-party frameworks and SDKs — typically as plugins, contrib modules, or starter libraries. This file is the catalog. Each integration has a dedicated reference under `references/python/integrations/`.

## How to use this catalog

1. Find the row matching the framework, SDK, or library the user is working with.
2. Read the linked reference file for setup, APIs, and pitfalls.
3. Cross-check the **Related** column — for AI/LLM integrations, also read [Temporal AI integration patterns](core/ai-patterns.md) and the language's `ai-patterns.md`.

## Catalog

| Integration | Language(s) | What it does | Reference | Related |
| -- | -- | -- | -- | -- |
| OpenAI Agents SDK (`temporalio.contrib.openai_agents`) | Python | Durable OpenAI Agents SDK agents: model calls run as Activities via `OpenAIAgentsPlugin`; tools are Activities (`activity_as_tool`) or workflow-resident `@function_tool`s; stateless/stateful MCP, sandbox backends, streaming, and OpenTelemetry export are supported | [OpenAI Agents SDK Python integration guide](python/integrations/openai-agents-sdk.md) | [Python AI integration patterns](python/ai-patterns.md), [Temporal AI integration patterns](core/ai-patterns.md) |
| LangSmith tracing (`temporalio.contrib.langsmith`) | Python | Experimental Temporal Plugin that propagates LangSmith trace context across Worker boundaries; lets `@traceable` run inside Workflows and Activities | [LangSmith Python integration guide](python/integrations/langsmith.md) | [Python AI integration patterns](python/ai-patterns.md), [Temporal AI integration patterns](core/ai-patterns.md) |
| LangGraph (`temporalio.contrib.langgraph`, Pre-release) | Python | Runs LangGraph Graph-API and Functional-API code as Temporal Workflows - nodes/tasks can execute as either in-workflow or as Activities | [LangGraph Python integration guide](python/integrations/langgraph.md) | [Python AI integration patterns](python/ai-patterns.md), [Temporal AI integration patterns](core/ai-patterns.md) |
| Google ADK (`temporalio[google-adk]`) | Python | Durable Google ADK agents: model calls run through `TemporalModel`-wrapped Activities, tools via `activity_tool`, MCP toolsets via `TemporalMcpToolSet` | [Google ADK Python integration guide](python/integrations/google-adk.md) | [Python AI integration patterns](python/ai-patterns.md), [Temporal AI integration patterns](core/ai-patterns.md) |
| Pydantic AI (`pydantic-ai[temporal]`) | Python | Durable agents through the `TemporalDurability` capability, with model requests, tool calls, and MCP communication executed as Temporal Activities | [Pydantic AI Python integration guide](python/integrations/pydantic-ai.md) | [Python AI integration patterns](python/ai-patterns.md), [Temporal AI integration patterns](core/ai-patterns.md) |
| OpenTelemetry (`temporalio[opentelemetry]`) | Python | Distributed tracing for Temporal apps with OpenTelemetry | [OpenTelemetry Python integration guide](python/integrations/opentelemetry.md) | [Python observability guide](python/observability.md) |
| Braintrust (`braintrust[temporal]`, Public Preview) | Python | LLM observability + prompt management: `BraintrustPlugin` traces every Workflow/Activity, `wrap_openai` captures LLM calls, `start_span` adds custom context, `load_prompt` fetches Braintrust-managed prompts | [Braintrust Python integration guide](python/integrations/braintrust.md) | [Python AI integration patterns](python/ai-patterns.md), [Temporal AI integration patterns](core/ai-patterns.md) |
