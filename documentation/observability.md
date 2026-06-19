# Observability

EcoSystem ships with built-in telemetry (see [statistics_keeper.md](statistics_keeper.md)) and
opt-in observability packages for metrics, traces, and logs via a professional open-source stack.

---

## The stack

| Tool              | Role                 | Licence     |
|-------------------|----------------------|-------------|
| Prometheus        | Metrics storage      | Apache 2.0  |
| Pushgateway       | Metrics entry point  | Apache 2.0  |
| Jaeger            | Distributed tracing  | Apache 2.0  |
| Loki              | Log aggregation      | AGPLv3/BSL  |
| Alloy             | Log + metrics agent  | Apache 2.0  |
| Grafana           | Dashboards           | AGPLv3/BSL  |

The central stack (Prometheus, Pushgateway, Loki, Jaeger, Grafana) runs on one machine via
docker-compose. Alloy is an agent installed on each machine where EcoSystem apps run.

For details on how to get this stack running in a docker image, see [observability/prometheus_grafana_jaeger_loki.md](observability/prometheus_grafana_jaeger_loki.md).

Start the stack:
```bash
export GRAFANA_ADMIN_PASSWORD=yourpassword
docker compose -f docker-compose.yml up -d
```

---

## Metrics -- ekosis-prometheus

`ekosis-prometheus` is a standalone EcoSystem application. It discovers local services via
`ECOENV_TCP/UDP/UDS_*` environment variables, polls `eco.statistics.get` (type: `gathered`)
at the gather period interval, and pushes to Pushgateway.

Install:
```bash
pip install -e ekosis_prometheus/
```

Wire into your start script alongside your services:
```bash
$VENV_BIN/ekosis_prometheus -i 0 -lfo &
```

Config via `ECOENV_EXTRA_*`:
- `ECOENV_EXTRA_PUSHGATEWAY` -- Pushgateway URL, e.g. `http://<YOUR HOST NAME>:9091`
- `ECOENV_EXTRA_JOB_NAME` -- push group name (default: `{app_name}-{instance}`)

To monitor ekosis-prometheus itself, give it a UDP port and include it in discovery:
```bash
ECOENV_UDP_EKOSIS_PROMETHEUS_0=127.0.0.1:8800
```

### Metrics exposed

| Metric                                   | Labels                             | Description                              |
|------------------------------------------|------------------------------------|------------------------------------------|
| `ekosis_service_health`                  | service, instance                  | 1 = UP, 0 = DOWN (poll failed)           |
| `ekosis_uptime_seconds`                  | service, instance                  | Seconds since startup                    |
| `ekosis_gather_period_seconds`           | service, instance                  | Statistics gather period in seconds      |
| `ekosis_endpoint_call_count`             | service, instance, group, endpoint | Calls in the last gather period          |
| `ekosis_endpoint_p95_seconds`            | service, instance, group, endpoint | 95th percentile response time            |
| `ekosis_endpoint_p99_seconds`            | service, instance, group, endpoint | 99th percentile response time            |
| `ekosis_buffered_endpoint_queue_pending` | service, instance, group, endpoint | Items pending in buffered endpoint queue |
| `ekosis_buffered_endpoint_queue_error`   | service, instance, group, endpoint | Items in buffered endpoint error queue   |
| `ekosis_buffered_sender_queue_pending`   | service, instance, group, endpoint | Items pending in buffered sender queue   |
| `ekosis_buffered_sender_queue_error`     | service, instance, group, endpoint | Items in buffered sender error queue     |
| `ekosis_custom_*`                        | service, instance                  | Custom statistics (via StatisticsKeeper) |

`group` is the route key prefix (e.g. `tracker` in `tracker.log_request_fail`).
`service` and `instance` are read from the stats response itself (`application.name` /
`application.instance`) -- not from service discovery env vars -- so they always match
what the service knows about itself.

EcoSystem internal endpoints (`eco.*` group) are excluded by default. To include them,
pass `exclude_groups=set()` to `translate_gathered_stats`.

---

## Tracing -- ekosis-otlp-traces

`ekosis-otlp-traces` wires OpenTelemetry tracing into EcoSystem via the middleware system.
Every endpoint in a service is automatically traced -- zero changes to endpoint code.

Install:
```bash
pip install -e ekosis_otlp_traces/
```

Wire into your application setup (one import, one call):
```python
from ekosis_otlp_traces.setup import initiate_otlp_tracing

initiate_otlp_tracing()
```

Config via `ECOENV_EXTRA_*`:
- `ECOENV_EXTRA_OTLP_TRACES_ENDPOINT` -- OTLP HTTP endpoint, e.g. `http://<YOUR HOST NAME>:4318/v1/traces`

Service name auto-derives from `{app_name}-{instance}` (e.g. `tracker-0`).

Span structure for a buffered endpoint request that fails then succeeds on retry:
```
receive span
  └── process attempt (retries=0, success=False)
  └── process attempt (retries=1, success=True)
```

Jaeger UI: `http://<YOUR HOST NAME>:16686`

---

## Logs -- Alloy

EcoSystem writes structured log files. Alloy ships them to Loki without any changes to
application code.

EcoSystem log format includes `application_name` and `application_instance` fields baked in.
In Grafana/Loki, you can query by `trace_id` (the chain-correlation half of a request's
`span_key`) to trace a full request chain across services.

Alloy config: `~/dev/learning_fix/observability_platform/alloy-config.production.alloy`

Install Alloy on each app server (not in the docker-compose stack):
```bash
# Grafana apt repo -- see observability_stack.md for full instructions
sudo apt install alloy
```

*NOTE*: There is an EcoSystem specific alternative to Alloy. For more on this
take a look at `ekosis_log_shipper` in the `ecosystem` repository.

---

## Grafana

Grafana: `http://<YOUR HOST NAME>:3000`

### EcoSystem Services dashboard

A provisioned dashboard is included at `provisioning/dashboards/ekosis.json`. It loads
automatically when the stack starts. Panels:

- **Service Overview** -- health (UP/DOWN) and uptime per service/instance
- **Endpoint Latency** -- P95 and P99 response time time series per endpoint
- **Throughput** -- two panels side by side:
  - *Request Rate (per second)* -- `ekosis_endpoint_call_count / ekosis_gather_period_seconds`.
    Because `call_count` resets to zero at the end of each gather period, dividing by
    `ekosis_gather_period_seconds` gives the correct per-second rate regardless of how the
    gather period is configured. Do not use `delta()` or `rate()` on `call_count` -- both
    produce incorrect results (negatives at period boundaries, underestimates mid-period).
  - *Call Count (per gather period)* -- the raw `ekosis_endpoint_call_count` value, showing
    the absolute number of calls accumulated since the last reset.
- **Buffered Queue Depths** -- pending and error queue sizes for buffered endpoints

Use the `Service` and `Instance` dropdowns to filter by specific services.

The dashboard is editable (`editable: true` in dashboards.yml). To persist edits:
export the JSON from Grafana (Dashboard → Share → Export) and replace `ekosis.json`.

---

## Licence risk and migration exits

Loki and Grafana are AGPLv3/BSL. Grafana Labs has already moved some products from open
licences to BSL once; it could happen again. The architectural hedge is to treat both as
swappable presentation layer -- all data lives in Prometheus (Apache 2.0) and Loki; if
either tool changes terms, the data stays and the tool gets replaced.

**Loki → VictoriaLogs:**
VictoriaLogs (Apache 2.0, from VictoriaMetrics) is the named exit for Loki. It speaks
LogQL and exposes a Grafana datasource plugin compatible with Loki's. Migration is a
one-afternoon job: swap the Loki container for VictoriaLogs, update the Grafana datasource
URL, existing dashboard queries continue to work unchanged.

**Grafana → TBD:**
No clean drop-in replacement exists yet for Grafana's dashboard layer. The hedge here is
dashboard JSON -- keep `ekosis.json` export-current so a migration to any future tool
starts from a documented panel definition rather than from scratch.

---

## Full example

`ecosystem/examples/observable_fun/` is a copy of `proper_fun` with full observability wired in.
It is the capstone example showing the complete integration. Run it with:

```bash
cd examples/observable_fun
./start_observable_fun.sh
```

The diff between `proper_fun` and `observable_fun` is the lesson.
