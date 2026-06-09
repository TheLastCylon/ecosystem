# Observability

EcoSystem exposes telemetry natively. Every service tracks uptime, endpoint call
counts, response time percentiles, and buffered queue depths out of the box: no
configuration required.

See [statistics_keeper.md](../statistics_keeper.md) for details.

Two optional packages bridge that telemetry to external observability backends:

| Package                                                                | What it does                                    |
|------------------------------------------------------------------------|-------------------------------------------------|
| [ekosis-jaeger-http](../../ekosis_jaeger_http/documentation/README.md) | Distributed tracing via Jaeger, using OTLP HTTP |
| [ekosis-prometheus](../../ekosis_prometheus/documentation/README.md)   | Metrics via Prometheus Pushgateway              |

These packages are opt-in. EcoSystem makes no demands on your observability tooling.

---

## Tested stacks

The following stacks have been tested with EcoSystem and are documented with setup
instructions, configuration files, and known gotchas. They are reference implementations,
not prescriptions.

As additional stacks are tested and supported, they will be added here.

| Stack                                                                                   | Status             |
|-----------------------------------------------------------------------------------------|--------------------|
| [Prometheus + Pushgateway + Jaeger + Loki + Grafana](prometheus_grafana_jaeger_loki.md) | Tested, documented |

---

## The observable_fun example

`examples/observable_fun/` is a copy of `proper_fun` with full observability wired
in. It is the capstone example for the complete EcoSystem observability integration.
The diff between `proper_fun` and `observable_fun` is the lesson.

---

## Licence risk

Loki and Grafana are AGPLv3/BSL. Grafana Labs has previously moved products from
open licences to BSL. The architectural hedge is to treat both as a swappable
presentation layer: Data lives in Prometheus and Loki. If licence terms change,
the data stays and the tool gets replaced.

**Loki vs. VictoriaLogs:** VictoriaLogs (Apache 2.0, from VictoriaMetrics) is the
named exit strategy. It speaks LogQL and exposes a Grafana datasource plugin
compatible with Loki. Migration is a one-afternoon job: swap the container, update
the datasource URL, existing dashboard queries work unchanged.

**Grafana → TBD:** No clean drop-in replacement currently exists. The hedge is to
keep `ekosis.json` export-current so any future migration starts from a documented
panel definition.
