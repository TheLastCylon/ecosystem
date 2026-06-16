# ekosis-prometheus

Prometheus metrics for EcoSystem applications, via Pushgateway.

Unlike [ekosis-otlp-traces](../../ekosis_otlp_traces/documentation/README.md),
this is not middleware. It is a standalone EcoSystem application that runs
alongside your services. It auto-discovers local services via environment
variables, polls their built-in telemetry endpoint, and pushes the results to
a Prometheus Pushgateway.

---

## How it works

Every EcoSystem service exposes a built-in `eco.statistics.get` endpoint.
`ekosis-prometheus` discovers local services by scanning the `ECOENV_TCP_*`,
`ECOENV_UDP_*`, and `ECOENV_UDS_*` environment variables already present in your
environment variables. It polls each service at the gather period interval and
pushes the resulting metrics to Pushgateway.

No changes to your services or their code are required. 😎

---

## Install

```bash
pip install ekosis-prometheus
```

---

## Running

`ekosis-prometheus` is a console script, run it alongside your services:

```bash
$VENV_BIN/ekosis_prometheus -i 0 -lfo &
```

It behaves like any other EcoSystem application, taking an instance number
(`-i 0`), logs to file (`-lfo`), and reads its configuration from `ECOENV_*`
environment variables.

---

## Configuration

```bash
ECOENV_EXTRA_PUSHGATEWAY=http://your-pushgateway-host:9091
```

| Variable                   | Default                 | Description                       |
|----------------------------|-------------------------|-----------------------------------|
| `ECOENV_EXTRA_PUSHGATEWAY` | (required)              | Pushgateway URL, including scheme |
| `ECOENV_EXTRA_JOB_NAME`    | `{app_name}-{instance}` | Push group name in Pushgateway    |

The poll interval matches the gather period configured for your services.
No separate timing configuration is needed.

---

## Service discovery

`ekosis-prometheus` discovers services by reading the same `ECOENV_TCP_*`,
`ECOENV_UDP_*`, and `ECOENV_UDS_*` environment variables used to configure your
EcoSystem applications.

**Only local services are discovered.** TCP and UDP addresses are included only
if the host resolves to `127.0.0.1`, `localhost`, `0.0.0.0`, the machine hostname,
or the machine's own IP address. Remote services are excluded. UDS paths are
always local by definition.

Service name and instance are parsed from the variable name:

| Environment variable             | name            | instance |
|----------------------------------|-----------------|----------|
| `ECOENV_TCP_ROUTER_0=...`        | `router`        | `0`      |
| `ECOENV_UDP_TIME_REPORTER_0=...` | `time_reporter` | `0`      |
| `ECOENV_UDS_TRACKER_1=...`       | `tracker`       | `1`      |

The rightmost `_N` segment is the instance number. Everything to the left is
the name, lowercased.

### Self-monitoring

To monitor `ekosis-prometheus` itself, give it a UDP port and it will discover
itself:

```bash
ECOENV_UDP_EKOSIS_PROMETHEUS_0=127.0.0.1:8800
```

---

## Metrics

| Metric                                   | Labels                              | Description                                 |
|------------------------------------------|-------------------------------------|---------------------------------------------|
| `ekosis_service_health`                  | service, instance                   | 1 = UP, 0 = DOWN (poll failed)              |
| `ekosis_uptime_seconds`                  | service, instance                   | Seconds since startup                       |
| `ekosis_gather_period_seconds`           | service, instance                   | Statistics gather period in seconds         |
| `ekosis_endpoint_call_count`             | service, instance, group, endpoint  | Calls accumulated in the last gather period |
| `ekosis_endpoint_p95_seconds`            | service, instance, group, endpoint  | 95th percentile response time               |
| `ekosis_endpoint_p99_seconds`            | service, instance, group, endpoint  | 99th percentile response time               |
| `ekosis_buffered_endpoint_queue_pending` | service, instance, group, endpoint  | Items pending in buffered endpoint queue    |
| `ekosis_buffered_endpoint_queue_error`   | service, instance, group, endpoint  | Items in buffered endpoint error queue      |
| `ekosis_buffered_sender_queue_pending`   | service, instance, group, endpoint  | Items pending in buffered sender queue      |
| `ekosis_buffered_sender_queue_error`     | service, instance, group, endpoint  | Items in buffered sender error queue        |
| `ekosis_custom_*`                        | service, instance                   | Custom statistics (via `StatisticsKeeper`)  |

`group` is the route key prefix (e.g. `tracker` from `tracker.log_request`).
`service` and `instance` are read from the stats-response itself. The service
knows its own identity, so these always match what the service reports, regardless
of how it was discovered.

EcoSystem internal endpoints (`eco.*` group) are excluded by default to keep
Prometheus and Grafana clean.

### Getting request rate from call_count

`ekosis_endpoint_call_count` resets to zero at the end of each gather period. This
means `delta()` and `rate()` both produce incorrect results. Negatives at period
boundaries, underestimates mid-period.

The correct Prometheus query for requests per second:

```
ekosis_endpoint_call_count / on(service, instance) group_left() ekosis_gather_period_seconds
```

This gives the correct per-second rate regardless of how the gather period is
configured.

To see the raw call count per gather period (useful for low-traffic services):

```
ekosis_endpoint_call_count
```

---

## Dependencies

| Package              | Licence    |
|----------------------|------------|
| prometheus-client    | Apache 2.0 |
