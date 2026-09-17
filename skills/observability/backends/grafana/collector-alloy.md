# Grafana Alloy: the same collector file once

Stamp: Grafana Alloy component references `otelcol.receiver.otlp`,
`otelcol.exporter.otlphttp`, `otelcol.exporter.debug`,
`otelcol.connector.spanmetrics`, `otelcol.connector.servicegraph`, the CLI
and Linux configuration pages at latest, read 2026-09-17.

Read `collector.md` first. This file only translates its known-good config
into Alloy syntax. Every verdict, rule and error there applies unchanged.

## The file

Alloy is the collector with a different syntax. The equivalent of the
metrics-generator verdict, in `/etc/alloy/config.alloy`:

```alloy
otelcol.receiver.otlp "default" {
  grpc { endpoint = "0.0.0.0:4317" }       // default 0.0.0.0:4317
  http { endpoint = "0.0.0.0:4318" }       // default 0.0.0.0:4318
  output {
    traces  = [otelcol.processor.batch.default.input]
    metrics = [otelcol.processor.batch.default.input]
    logs    = [otelcol.processor.batch.default.input]
  }
}

otelcol.processor.batch "default" {
  output {
    traces  = [otelcol.exporter.otlphttp.tempo.input, otelcol.exporter.debug.default.input]
    metrics = [otelcol.exporter.otlphttp.prometheus.input]
    logs    = [otelcol.exporter.otlphttp.loki.input]
  }
}

otelcol.exporter.otlphttp "tempo" {
  client {
    endpoint = "http://tempo:4318"            // appends /v1/traces
    tls { insecure = true }
  }
}

otelcol.exporter.otlphttp "loki" {
  client {
    endpoint = "http://loki:3100/otlp"        // appends /v1/logs
    headers  = { "X-Scope-OrgID" = sys.env("TENANT") }
  }
}

otelcol.exporter.otlphttp "prometheus" {
  client {
    endpoint = "http://prometheus:9090/api/v1/otlp"   // appends /v1/metrics
  }
}

otelcol.exporter.debug "default" {
  verbosity = "detailed"                      // stderr, like the collector
}
```

`otelcol.connector.spanmetrics` and `otelcol.connector.servicegraph` exist
with the same arguments as the connectors above, `dimension { name = "..." }`
and `histogram { unit = "s" }`, `store { ttl = "10s" max_items = 10000 }`,
`virtual_node_peer_attributes`. Same rule: only under the connectors verdict.


## Running it

```sh
alloy validate /etc/alloy/config.alloy
alloy run /etc/alloy/config.alloy            # UI on 127.0.0.1:12345 by default
sudo systemctl restart alloy                 # package install
sudo journalctl -u alloy                     # its logs and the debug exporter's output
```

Extra flags go in `CUSTOM_ARGS` in `/etc/default/alloy` on Debian and Ubuntu,
`/etc/sysconfig/alloy` on RHEL, Fedora and SUSE. To reach the UI from another
host add `--server.http.listen-addr=0.0.0.0:12345`. The UI home page lists
every component and its health; a red exporter names the endpoint it cannot
reach.

## Never

- Never mix an Alloy and a collector in front of the same stores without
  writing both files into the vocabulary. Two relays, one spelling column
  each.

## Stop and ask

- The Alloy config was converted from a collector file with
  `--config.format=otelcol` and a component is missing from the UI. A person
  compares the two files.
