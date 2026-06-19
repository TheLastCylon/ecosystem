# Distributed tracking (Request tracking)

In distributed systems, one of the biggest time wasters is having to debug a
system where you can't track the messages from one component to another. Anyone
who has been in this situation, will be able to discuss the pain of it, in
excruciating detail.

With EcoSystem however, you can bypass this entire situation, with ease.

If you examine [the protocol](./the_protocol.md), you'll notice both the
request and response DTOs, have a `span_key` field. This is what you want to get
your hands on, from within your code.

When you decorate a function with `sender` or `buffered_sender`, the request
gets a UUID generated for it, by default.

You can also, take complete control over the UUID being used for sending,
and propagate it throughout your entire system. Thus enabling you to log and
track entire communication chains.

The functions you decorate with `endpoint` or `buffered_endpoint` will receive this
`span_key` parameter it gets invoked with, from within the framework.

The [Fun Factory example system](./examples/fun_factory/fun_factory.md),
demonstrates this.

What follows here, is a brief description of how all this is achieved.

## Your sender functions

Take a look at the signature of the `sender_app_process_message` function, in
[examples/fun_factory/router/client.py](../examples/fun_factory/router/client.py).

```python
# --------------------------------------------------------------------------------
@sender(router_client, "app.process_message", RouterResponseDto)
async def sender_app_process_message(message: str, **kwargs):
    return RouterRequestDto(request=message)
```

You'll notice the parameter list includes `**kwargs`. 

Do this with your own sender functions, and you'll be able to invoke them with the
`span_key` parameter. Like so:

```python
response: RouterResponseDto = await sender_app_process_message(message, span_key=span_key)
```

As you can see, `span_key` is being set to a predetermined value, rather than having
EcoSystem create one.

The exact same can be done for your functions, decorated with `buffered_sender`.

All you have to do is:
1. Make sure your function definition has `**kwargs` in the parameter list.
2. Set `span_key` to your desired value, where you call the function.

## Your endpoint functions

Take a look at the `process_message` function, in
[examples/fun_factory/router/endpoints.py](../examples/fun_factory/router/endpoints.py).

```python
# --------------------------------------------------------------------------------
@endpoint("app.process_message", RouterRequestDto)
async def process_message(span_key : SpanKey, dto: RouterRequestDto) -> PydanticBaseModel:
    _log_request(span_key, dto.request, time.time())
    log.info(f"RCV: span_key[{span_key}]")
    request_data = dto.request.split(" ")

    if "fortune" == request_data[0].strip().lower():
        response = await _get_fortune(span_key)
    elif "joke" == request_data[0].strip().lower():
        response = await _get_joke(span_key)
    elif "lotto" == request_data[0].strip().lower():
        response = await _get_lotto(span_key, request_data)
    elif "time" == request_data[0].strip().lower():
        response = await _get_time(span_key)
    else:
        response = await _get_prediction(span_key, dto.request)

    log.info(f"RSP: span_key[{span_key}]")
    _log_response(span_key, response, time.time())
    return RouterResponseDto(response=response)
```

You'll notice the `span_key` parameter. In the function signature.

When you want to have access to the `span_key` within your endpoint,
you simple add it as a paramter for your endpoint function.

Moving along with the example though:

You'll note `span_key` is passed on, to all the various helper functions, as
well as the invocations of `_log_request` and `_log_response`.

While also being logged in `process_message` with:
- `log.info(f"RCV: span_key[{span_key}]")` and
- `log.info(f"RSP: span_key[{span_key}]")`

This is how you get your logs/traces to show the value of `span_key` and
propagate it through your entire system.

The steps are:
1. Make sure `span_key` is in your `endpoint` or `buffered_endpoint function`
   signature.
2. Pass it on deeper into your own code if needed.

Using this, will allow you to track entire message chains, regardless of how big
your system becomes. So, take it from those of us who have had to deal with this
pain:

Use this feature. Use it liberally. You'll thank yourself later.
