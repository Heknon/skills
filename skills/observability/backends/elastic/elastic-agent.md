# APM Server under Elastic Agent and Fleet

Stamp: Elastic 8.17 to 8.19 docs, read 2026-09-17. 9.x notes at the end.

**Verdict you produce:** the APM Server URL the SDK or collector must send to,
the auth scheme in use, `Bearer` or `ApiKey`, and the Fleet integration
version. Write them into `vocabulary.md` under `backend:` and
`verified against:`.

## Where the settings live

APM Server is not a daemon with an `apm-server.yml` on disk. It is the
**Elastic APM integration** inside an Elastic Agent policy, and Elastic Agent
runs it as one of its components. Every setting is edited in Kibana:

**Fleet** > **Agent policies** > the policy > **Elastic APM** > **Actions** >
**Edit integration**.

Fleet pushes the change to the agent. There is nothing to restart by hand. The
`apm-server.*` keys below are the names the same settings have in a standalone
`apm-server.yml`, and the names you see in `elastic-agent inspect` output.

## Settings that matter

| Fleet UI name | `apm-server.yml` key | Default | Why it matters |
| --- | --- | --- | --- |
| Host | `apm-server.host` | `localhost:8200` | what APM Server binds; `localhost` refuses other hosts |
| URL | none, Cloud only | fixed | the address agents use on Elastic Cloud; not editable there |
| Secret token, under Agent authorization | `apm-server.auth.secret_token` | empty | sent as `Authorization: Bearer <token>`; plain text, so only meaningful with TLS |
| API key for agent authentication | `apm-server.auth.api_key.enabled` | `false` | sent as `Authorization: ApiKey <base64 of id:key>`. `UNVERIFIED:` exact UI label |
| Number of keys | `apm-server.auth.api_key.limit` | `50` | distinct keys accepted per minute. `UNVERIFIED:` exact UI label |
| Anonymous Agent access | `apm-server.auth.anonymous.enabled` | `false` | lets unauthenticated agents in; RUM needs it |
| Enable RUM | `apm-server.rum.enabled` | `false` | browser agents; irrelevant to a Python harness |
| Default Service Environment | `apm-server.default_service_environment` | none | `service.environment` for data that carries no `deployment.environment` |
| Capture personal data | `apm-server.capture_personal_data` | `true` | keeps `client.ip` and `user_agent`; turn off for privacy |
| Maximum size per event | `apm-server.max_event_size` | `307200` bytes | one span larger than this is rejected; huge attributes hit it |
| Enable tail-based sampling | `sampling.tail.enabled` | `false` | APM Server decides per whole trace after it ends |
| Interval | `sampling.tail.interval` | `1m` | how often sampling decisions are synchronised between APM Servers |
| Policies | `sampling.tail.policies` | none | list of `sample_rate` with optional `service.name`, `service.environment`, `trace.name`, `trace.outcome`; last entry must be a bare `sample_rate` |
| Storage limit | `sampling.tail.storage_limit` | `3GB` | local disk for undecided traces |
| TTL | `sampling.tail.ttl` | `30m` | how long an undecided trace is kept |
| SSL/TLS input settings | `apm-server.ssl.enabled`, `apm-server.ssl.certificate`, `apm-server.ssl.key` | off | TLS between SDK or collector and APM Server |

Tail sampling policies example, in the **Policies** field:

```yaml
- sample_rate: 1.0
  trace.outcome: failure
- sample_rate: 0.1
```

## The OTLP URL

APM Server serves OTLP/gRPC and OTLP/HTTP on the **same port** as the classic
agent protocol, the one in **Host**, by default `8200`. There is no separate
OTLP port. So:

- gRPC: `endpoint: apm-server-host:8200`, no scheme, no path.
- HTTP: `OTEL_EXPORTER_OTLP_ENDPOINT=http://apm-server-host:8200`; the SDK and
  the `otlphttp` exporter append `/v1/traces`, `/v1/metrics`, `/v1/logs`.
  `UNVERIFIED:` the user docs say only "host and port"; the paths are the
  standard OTLP/HTTP paths and the apm-server repository lists them.
- Header, one space after the scheme word:
  `Authorization=Bearer an_apm_secret_token` or
  `Authorization=ApiKey an_api_key` in `OTEL_EXPORTER_OTLP_HEADERS`.

## Is it healthy

1. Kibana: **Fleet** > **Agents**. The agent's status must read **Healthy**.
   Anything else, `Unhealthy`, `Offline`, `Updating`, means APM Server may
   not be listening.
2. On the agent host:

   ```sh
   sudo elastic-agent status                 # agent state and each component's state
   sudo elastic-agent status --output full   # per unit detail
   sudo elastic-agent status --output yaml   # machine readable
   ```

   The component list must show the APM component as `HEALTHY`.
   `UNVERIFIED:` the component id is `apm-default`; the monitoring docs name
   the process `apm-server-default`.
3. What it is actually running with:

   ```sh
   sudo elastic-agent inspect                            # the whole policy as the agent has it
   sudo elastic-agent inspect components --show-config   # every component with its rendered config
   ```

   Look for `apm-server:` and check `host`, `auth`, `sampling`. This is
   read-only. Editing anything it prints changes nothing.
4. Version, both halves:

   ```sh
   sudo elastic-agent version
   ```

   and in Kibana **Integrations** > **Installed integrations** > **Elastic
   APM** > **Settings** for the integration version. **Upgrade to latest
   version** there also upgrades the integration policies when the box is
   left ticked. Write both numbers into `vocabulary.md`.

## APM Server's own log lines

APM Server writes into the agent's log files. On a Linux install from the
tarball:

```
/opt/Elastic/Agent/data/elastic-agent-*/logs/elastic-agent-YYYYMMDD.ndjson
```

With the deb or rpm package the same files are under
`/var/lib/elastic-agent/data/elastic-agent-*/logs/`. One JSON object per line;
filter on the component:

```sh
sudo elastic-agent logs -f -n 200 -C apm-default       # UNVERIFIED: component name apm-default
grep '"component":{"id":"apm-default"' /opt/Elastic/Agent/data/elastic-agent-*/logs/elastic-agent-*.ndjson | tail
```

In Kibana: **Fleet** > **Agents** > the agent > **Logs** tab > dataset
`elastic_agent.apm_server`. That is where a rejected request, a wrong token,
and an Elasticsearch bulk failure are written. `verification-ladder.md` rung
3 says which lines to look for.

## Standalone APM Server, one paragraph

The `apm-server` binary reads `apm-server.yml` from its install directory,
holds the same keys under `apm-server.*`, `output.elasticsearch.*` and
`sampling.tail.*`, is started with `apm-server -e -c apm-server.yml`, and
logs to stderr with `-e`. It supports outputs Fleet does not, Logstash and
Kafka among them, and it is where `apm-server test config` and
`apm-server test output` exist. Nothing in the vocabulary changes between the
two: same fields, same renames, same data streams. Only the place you edit
settings changes.

## What cannot be changed under Fleet

- The output. Fleet-managed APM Server writes to Elasticsearch or
  Elasticsearch Service only; the output is the agent policy's output, not a
  setting of the integration.
- Anything not exposed in the integration policy editor. There is no file to
  add a key to. If the setting is not in the table above or the editor's
  advanced section, it is not available.
- **URL** on Elastic Cloud. It is fixed by the deployment.
- The running config on disk. `elastic-agent inspect` prints it; edits to the
  files under `data/` are overwritten on the next policy check-in.

## Never

- Never write an `apm-server.yml` on a Fleet-managed host and expect it to be
  read. It is not.
- Never point the SDK at a port other than **Host**'s for OTLP.
- Never put a secret token in `vocabulary.md`. Record the scheme, not the value.

## Stop and ask

- The agent shows **Healthy** but `inspect components` shows no `apm-server`
  block. The integration is not in this policy.
- Two agents run the APM integration and tail sampling is on. Both must share
  the same Elasticsearch and the same **Interval**; a person confirms it.

## Elastic 9.x

From 9.0 `sampling.tail.storage_limit` defaults to unlimited and APM Server
stops writing at 80 percent disk usage instead. From 9.2 Elastic Agent
carries an OpenTelemetry Collector, and from 9.5 the EDOT Collector is that
built-in one; it can bypass APM Server and write OTel-native data streams, a
different spelling, see `collector.md`.
