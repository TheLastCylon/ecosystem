# ekosis-otlp-traces

OTLP HTTP distributed tracing for EcoSystem applications (Jaeger, Tempo, or any other
OTLP-compatible backend).

Wires into the EcoSystem [middleware](../../documentation/middleware.md) system. Every endpoint
in a service is automatically traced. No changes to endpoint-code required. 😎

---

## How it works

Every EcoSystem request carries a `span_key` (`trace_id` + `span_id`). `ekosis-otlp-traces`
reads `span_key.trace_id` as the OTel trace ID, so one `span_key`, one trace, full distributed
trace visible across all services -- regardless of how many hops the request takes.

For regular endpoints, a span opens when the request arrives (`before_routing`) and closes
when the response is sent (`after_routing`). For buffered endpoints, the receive span is linked
to child process spans via the metadata mechanism, so the trace survives the async gap between
queuing and processing, including across retries.

---

## Install

```bash
pip install ekosis-otlp-traces
```

---

## Configuration

Set the OTLP HTTP traces endpoint via `ECOENV_EXTRA_*`:

```bash
ECOENV_EXTRA_OTLP_TRACES_ENDPOINT=http://your-otlp-host:4318/v1/traces
```

The service name in your tracing backend auto-derives from `{app_name}-{instance}` (e.g.
`tracker-0`). No explicit configuration required.

---

## Wiring

### Setup helper (recommended)

```python
from ekosis_otlp_traces.setup import initiate_otlp_tracing

initiate_otlp_tracing()
```

One call. Reads `ECOENV_EXTRA_OTLP_TRACES_ENDPOINT`, creates both middleware instances, and
registers them with `MiddlewareManager` and `BufferedMiddlewareManager`.

Place the call before `app.start()`, typically at the top of your application's `__init__`:

```python
from ekosis.application_base    import ApplicationBase
from ekosis_otlp_traces.setup   import initiate_otlp_tracing

initiate_otlp_tracing()

# --------------------------------------------------------------------------------
class MyServer(ApplicationBase):
    def __init__(self):
        super().__init__()

# --------------------------------------------------------------------------------
def main():
    with MyServer() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
```

### Manual wiring

If you need access to the middleware instances directly (for example, to compose
with your own middleware):

```python
from ekosis.middleware       import MiddlewareManager, BufferedMiddlewareManager
from ekosis_otlp_traces      import OtlpTracingMiddleware, OtlpBufferedTracingMiddleware

tracer = OtlpTracingMiddleware(endpoint="http://your-otlp-host:4318/v1/traces")
MiddlewareManager().add(tracer)
BufferedMiddlewareManager().add(OtlpBufferedTracingMiddleware(tracer))
```

`OtlpBufferedTracingMiddleware` takes the `OtlpTracingMiddleware` instance as an argument.
It is used to retrieve the active receive-span at push time and link the process spans to it.

---

## Span structure

### Regular endpoint

One span per request, named with the route key:

```
tracker.log_request     (trace_id = span_key.trace_id)
  |
  +-> request.trace_id  = "3f2a1b..."
  +-> request.span_id   = "9c7e..."
  +-> request.route_key = "tracker.log_request"
```

### Buffered endpoint

The receive span is the root. Each process attempt (including retries) produces a child
span linked back to the receive span via the persisted span id, carried through
`PendingEntry.metadata`:

```
tracker.log_request_fail        (receive span)
  |
  +-> LogRequestFailDTO.process (retries=0, process.success=False)
  |
  +-> LogRequestFailDTO.process (retries=1, process.success=True)
```

The child span name is the DTO class name + `.process`. The `retries` attribute
shows which attempt produced the span. `process.success=False` means the item
was returned to the queue for retry or moved to the error queue.

If the receive span is no longer in memory when a process attempt runs (e.g. after a
restart), the process span falls back to using `span_key.span_id` as its own parent --
it stays in-trace rather than becoming orphaned, it just can't be linked back to a
receive span that no longer exists.

---

## Dependencies

| Package                                    | Licence    |
|--------------------------------------------|------------|
| opentelemetry-api                          | Apache 2.0 |
| opentelemetry-sdk                          | Apache 2.0 |
| opentelemetry-exporter-otlp-proto-http     | Apache 2.0 |
