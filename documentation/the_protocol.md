# The protocol

Right now, EcoSystem's protocol is pure JSON, there are plans to have a binary
protocol option available, but while architecture decisions are being made, JSON
will be used to test and validate decisions. Once this process is complete, the
aim is to make other wire-protocols available. This includes but is not limited
to gRPC.

With one of EcoSystem's core tenants being observability, the protocol itself
has to support this. As such, there are some things that are simply not optional.

The wire-protocol code can be found in
[ekosis/data_transfer_objects/json_protocol.py](../ekosis/data_transfer_objects/json_protocol.py),
and yes, they are exactly as simple as they appear.

As a user, it's unlikely that you'll have to deal with this directly, but what
follows is good to know when it comes to debugging your applications.

---

## The Request DTO

```python
57: class RequestDTO(PydanticBaseModel):
58:     route_key: str
59:     span_key : SpanKey
60:     data     : Any
```

### `route_key`
This is the identifier used by EcoSystem, to route a request to your custom code.
This is equivalent to what some would call an "endpoint" in other frameworks. It can
be any string you can type on a keyboard, as long as it is unique within your
application and is allowed to act as a Python dictionary key, it will be valid.

### `span_key`
This is a unique identifier for a request.

*BUT IT GOES WAY BEYOND THAT!!*

A SpanKey object has two fields:
```python
 9:     trace_id : uuid.UUID
10:     span_id  : SpanId
```

The `trace_id` is a UUID, and maps directly to the trace_id of the Open Telemetry
specification.

The `span_id` is a 64-bit integer that maps directly to the span_id of the Open
Telemetry specification. Within the JSON protocol, the `span_id` is represented
as a 16-byte hexadecimal string.

Yes, EcoSystem supports standardised observability, at protocol level.

Importing open telemetry libraries IS OPTIONAL!

You do not have to use open telemetry at all, but the EcoSystem protocol has `span_key` as a basis for
uniquely identifying requests, wither open telemetry is used or not.

### `data`

This has a data type of Any, it can really be any valid JSON, and is used to contain the
data you need to send to the handler that is going to deal with your request.

The JSON string for a response could look like this:

```json
{
  "route_key": "some_string",
  "span_key" : {
    "trace_id" : "12345678-1234-1234-1234-1234567890ab",
    "span_id"  : "1234567890abcdef"
  },
  "data"     : {}
}
```

## The Response DTO

```python
63: class ResponseDTO(PydanticBaseModel):
64:     span_key: SpanKey | None = None
65:     status  : int
66:     data    : Any
```

### `span_key`
This is the same as the `span_key` in the request DTO.

### `status`

This is an integer reflecting the status of your request. A value of 0 will always
indicate success. The exact meanings for other can be found in the source at:
[ekosis/requests/status.py](../ekosis/requests/status.py).

### `data`
This will contain the response data, it could be any valid JSON.

## Conclusion
Yea, that's it. The EcoSystem JSON wire-protocol in full.
Simple, effective, no mess, no fuss.
