# Distributed tracking (Request tracking)

In distributed systems, one of the biggest time wasters is having to debug a
system where you can't track the messages from one component to another. Anyone
who has had to deal with this, will be able to discuss the pain of having to
deal with this, in excruciating detail.

With Ecosystem however, you can bypass this entire situation, with ease.

If you examine [the protocol](./the_protocol.md), you'll notice both the
request and response DTOs, have a `uid` field. This is what you want to get
your hands on, from within your code.

When you decorate a function with `sender` or `queued_sender`, the request
gets a UUID generated for it, by default.

You can also, take complete control over the UUID being used for sending,
and propagate it throughout your entire system. Thus enabling you to log and
track entire communication chains.

The functions you decorate with `endpoint` or `queued_endpoint` will receive this
UUID in the `request_uuid` parameter it gets invoked with, from within the
framework.

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
`request_uid` parameter. Like so:

```python
response: RouterResponseDto = await sender_app_process_message(message, request_uid=uuid_to_use)
```

As you can see, `request_uid` is being set to a predetermined UUID, rather than having
Ecosystem create one.

The exact same can be done for your functions, decorated with `queued_sender`.

All you have to do is:
1. Make sure your function definition has `**kwargs` in the parameter list.
2. Set `request_uid` to your desired UUID, where you call the function.

## Your endpoint functions

Take a look at the `process_message` function, in
[examples/fun_factory/router/endpoints.py](../examples/fun_factory/router/endpoints.py).

```python
# --------------------------------------------------------------------------------
@endpoint("app.process_message", RouterRequestDto)
async def process_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
    request_data_raw = cast(RouterRequestDto, request)
    _log_request(request_uuid, request_data_raw.request, time.time())
    log.info(f"RCV: request_uuid[{request_uuid}]")
    request_data = request_data_raw.request.split(" ")

    if "fortune" == request_data[0].strip().lower():
        response = await _get_fortune(request_uuid)
    elif "joke" == request_data[0].strip().lower():
        response = await _get_joke(request_uuid)
    elif "lotto" == request_data[0].strip().lower():
        response = await _get_lotto(request_uuid, request_data)
    elif "time" == request_data[0].strip().lower():
        response = await _get_time(request_uuid)
    else:
        response = await _get_prediction(request_uuid, request_data_raw.request)

    log.info(f"RSP: request_uuid[{request_uuid}]")
    _log_response(request_uuid, response, time.time())
    return RouterResponseDto(response=response)
```

You'll notice the `request_uuid` parameter. In the function signature.

Yes, all your endpoint function have to be able to accept that parameter.

Wither you use it in your endpoint function or not, does not matter. They all
have to be able to receive that parameter when called. And yes, the framework
forces you to have it there, rather than as a `**kwargs` parameter. Exactly
because we want the choice **not** to use it, to be an explicit, and very visible
choice.

Moving along with the example though:

You'll note `request_uuid` is passed on, to all the various helper functions, as
well as the invocations of `_log_request` and `_log_response`.

While also being logged in `process_message` with:
- `log.info(f"RCV: request_uuid[{request_uuid}]")` and
- `log.info(f"RSP: request_uuid[{request_uuid}]")`

This is how you get your logs/traces to show the value of `request_uuid` and
propagate it through your entire system.

The steps are:
1. Use `request_uuid` in your logs/traces.
2. Make sure to pass it on to any sender functions that might get called, due
   to your endpoint function being invoked.

Using this, will allow you to track entire message chains, regardless of how big
your system becomes. So, take it from those of us who have had to deal with this
pain:

Use this feature. Use it liberally. You'll thank yourself later.
