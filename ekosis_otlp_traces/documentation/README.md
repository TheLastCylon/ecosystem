# ekosis-jaeger-http

Jaeger distributed tracing for EcoSystem applications, via OTLP HTTP.

Wires into the EcoSystem [middleware](../../documentation/middleware.md) system. Every endpoint
in a service is automatically traced. No changes to endpoint-code required. 😎

---

## How it works

Every EcoSystem request carries a `request_uid`, `ekosis-jaeger-http` uses that UUID as the Jaeger trace ID.
One `request_uid`, one trace, full distributed trace visible across all services.

For regular endpoints, a span opens when the request arrives (`before_routing`) and closes
when the response is sent (`after_routing`). For buffered endpoints, the receive span is linked
to child process spans via the metadata mechanism, so the trace survives the async gap between
queuing and processing, including across retries.

---

## Install

```bash
pip install ekosis-jaeger-http
```

---

## Configuration

Set the Jaeger OTLP HTTP endpoint via `ECOENV_EXTRA_*`:

```bash
ECOENV_EXTRA_JAEGER_ENDPOINT=http://your-jaeger-host:4318/v1/traces
```

The service name in Jaeger auto-derives from `{app_name}-{instance}` (e.g. `tracker-0`).
No explicit configuration required.

---

## Wiring

### Setup helper (recommended)

```python
from ekosis_jaeger_http.setup import initiate_jaeger_tracing

initiate_jaeger_tracing()
```

One call. Reads `ECOENV_EXTRA_JAEGER_ENDPOINT`, creates both middleware instances, and
registers them with `MiddlewareManager` and `BufferedMiddlewareManager`.

Place the call before `app.start()`, typically at the top of your application's `__init__`:

```python
from ekosis.application_base          import ApplicationBase
from ekosis_jaeger_http.setup         import initiate_jaeger_tracing

initiate_jaeger_tracing()

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
from ekosis.middleware                      import MiddlewareManager, BufferedMiddlewareManager
from ekosis_jaeger_http                     import JaegerHttpTracingMiddleware
from ekosis_jaeger_http.buffered_middleware import JaegerHttpBufferedTracingMiddleware

tracer = JaegerHttpTracingMiddleware(endpoint="http://your-jaeger-host:4318/v1/traces")
MiddlewareManager().add(tracer)
BufferedMiddlewareManager().add(JaegerHttpBufferedTracingMiddleware(tracer))
```

`JaegerHttpBufferedTracingMiddleware` takes the `JaegerHttpTracingMiddleware`
instance as an argument. It is used to retrieve the active receive-span at push
time and link the process spans to it.

---

## Span structure

### Regular endpoint

One span per request, named with the route key:

```
tracker.log_request     (trace_id = request_uid)
  |
  +-> request.uid       = "3f2a1b..."
  |
  +-> request.route_key = "tracker.log_request"
```

### Buffered endpoint

The receive span is the root. Each process attempt (including retries) produces a child
span linked back to the receive span via the persisted trace and span IDs:

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

---

## Dependencies

| Package                                    | Licence    |
|--------------------------------------------|------------|
| opentelemetry-api                          | Apache 2.0 |
| opentelemetry-sdk                          | Apache 2.0 |
| opentelemetry-exporter-otlp-proto-http     | Apache 2.0 |
