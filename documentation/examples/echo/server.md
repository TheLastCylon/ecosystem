# The obligatory Echo-server

If you've not looked at the [simplest Ecosystem server](../base.md), you might want to take a look at it. This example expands on that.

The code for this example is located in [examples/echo/server.py](../../../examples/echo/server.py)

To run it, get into your terminal and go to the directory you have cloned this repository into, then:

`python -m examples.echo.server -i 0`

On Linux you can execute a `netcat` command and test it.

For TCP:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "echo", "data": {"message": "This is a test"}}' | nc localhost 8888
```

For UDP:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "echo", "data": {"message": "This is a test"}}' | nc -u localhost 8889
```

For UDS:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "echo", "data": {"message": "This is a test"}}' | nc -U /tmp/echo_example_0_uds.sock
```

The response you get should be similar to:

```json
{"uid":"abcdef01-abcd-abcd-abcd-abcdef012345","status":0,"data":{"message":"This is a test"}}
```

## The code

As with all frameworks, we will now examine how to get a server to give you back, what you sent in.

Yes, an Ecosystem ... Echo-server.

**IMPORTANT:** This is not an example of good coding practice!
Project structure is important! Later on, we'll look at how to structure your Ecosystem projects, so you don't end up in maintenance-hell.
Right now though, it's more important for you to understand the basics. So don't use this as an example of how to lay out your projects.

Here's the code:

```python
 1: import uuid
 2: from pydantic import BaseModel as PydanticBaseModel
 3: 
 4: from ecosystem import ApplicationBase
 5: from ecosystem import ConfigApplication
 6: from ecosystem import ConfigApplicationInstance
 7: from ecosystem import ConfigTCP
 8: from ecosystem import ConfigUDP
 9: from ecosystem import ConfigUDS
10: from ecosystem import endpoint
11: 
12: 
13: # --------------------------------------------------------------------------------
14: class EchoRequestDto(PydanticBaseModel):
15:     message: str
16: 
17: 
18: # --------------------------------------------------------------------------------
19: class EchoResponseDto(PydanticBaseModel):
20:     message: str
21: 
22: 
23: # --------------------------------------------------------------------------------
24: @endpoint("echo", EchoRequestDto)
25: async def echo_this_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
26:     return EchoResponseDto(message = request.message)
27: 
28: 
29: # --------------------------------------------------------------------------------
30: app_config          = ConfigApplication(name = "echo_example")
31: app_instance_config = ConfigApplicationInstance(
32:     instance_id = "0",
33:     tcp         = ConfigTCP(host="127.0.0.1", port=8888),
34:     udp         = ConfigUDP(host="127.0.0.1", port=8889),
35:     uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
36: )
37: app_config.instances[app_instance_config.instance_id] = app_instance_config
38: 
39: 
40: # --------------------------------------------------------------------------------
41: class EchoExampleServer(ApplicationBase):
42:     def __init__(self):
43:         super().__init__(app_config.name, app_config)
44: 
45: 
46: # --------------------------------------------------------------------------------
47: def main():
48:     with EchoExampleServer() as app:
49:         app.start()
50: 
51: 
52: # --------------------------------------------------------------------------------
53: if __name__ == '__main__':
54:     try:
55:         main()
56:     except Exception as e:
57:         print(str(e))
58:
```

### Imports
Here lines 4 to 9 are exactly as lines 1 to 6 were in our [previous example](../base.md).

```python
 1: import uuid
 2: from pydantic import BaseModel as PydanticBaseModel
 3: 
 4: from ecosystem import ApplicationBase
 5: from ecosystem import ConfigApplication
 6: from ecosystem import ConfigApplicationInstance
 7: from ecosystem import ConfigTCP
 8: from ecosystem import ConfigUDP
 9: from ecosystem import ConfigUDS
10: from ecosystem import endpoint
```

Lines 1 and 2 are importing a few things we'll need.
1. Line 1 gives us the python `uuid` stuff we'll need with creating an endpoint.
2. Line 2 gives us the Pydantic base model.
   1. Note that I'm importing Pydantic's `BaseModel` class as `PydanticBaseModel`. Strictly speaking this isn't necessary for this example, but it sets a base-line for good development with Ecosystem.

On line 10, we import the Ecosystem `endpoint` decorator function. We'll be looking into that a bit further down.

### Declaring our Data Transfer Objects (DTOs for short)
Ecosystem uses Pydantic for all it's DTOs.
```python
13: # --------------------------------------------------------------------------------
14: class EchoRequestDto(PydanticBaseModel):
15:     message: str
16: 
17: 
18: # --------------------------------------------------------------------------------
19: class EchoResponseDto(PydanticBaseModel):
20:     message: str
```

As you can see here, we derive our DTOs from our import of Pydantic's `BaseModel` as `PydanticBaseModel`.

Strictly speaking, we could have used the same model for both requests and responses, but this is more complete and demonstrates the purpose of each, more clearly.

### The endpoint decorator
```python
23: # --------------------------------------------------------------------------------
24: @endpoint("echo", EchoRequestDto)
```

Here, on line 24, we use the Ecosystem `endpoint` decorator, to create an endpoint for us.

It expects two things:
1. A route key, in this case `"echo"`
2. A request type, as in the model that a request on this endpoint should honour. In this case, that is `EchoRequestDto`

So, what is a route key?

It is literally nothing more than a string, that gets used in Ecosystem's routing table, to map requests it receives, to your endpoint function.

Just about any string would be valid. If the string can be used as a key in a Python dictionary, and follows the rules of JSON, it's good to go.

So yea, a route key of something arbitrary like `"@@#99asdfaadf"` is completely valid. If you can type it on a keyboard, it will work.

Of course, just because you can do it, does not mean you should. Keep it sane!

IMPORTANT: A route key absolutely must be unique within your application. An Ecosystem application will not even start up if you attempt to create two endpoints with the same route key.

### The function
```python
25: async def echo_this_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
26:     return EchoResponseDto(message = request.message)
```
On line 25, we declare our endpoint function.

Yes, it must follow that signature. The parameter list and return type must match.

Of course, the function name may be any valid Python function name.

And yes, it must be an `async def` function. Ecosystem makes liberal use of Python's `asyncio`

On line 26, we generate our response and return it.
As you can see here, we do nothing more than instantiate an instance of `EchoResponseDto`, making sure to populate its `message` attribute, with what we received in the request.

### Configuration
From line 30 to 37, we do exactly what we did in our [previous example](../base.md).
The only difference here, is that our application name is `echo_example`.
```python
30: app_config          = ConfigApplication(name = "echo_example")
31: app_instance_config = ConfigApplicationInstance(
32:     instance_id = "0",
33:     tcp         = ConfigTCP(host="127.0.0.1", port=8888),
34:     udp         = ConfigUDP(host="127.0.0.1", port=8889),
35:     uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
36: )
37: app_config.instances[app_instance_config.instance_id] = app_instance_config
```

# Declaring the application class, and running it.
```python
40: # --------------------------------------------------------------------------------
41: class EchoExampleServer(ApplicationBase):
42:     def __init__(self):
43:         super().__init__(app_config.name, app_config)
44: 
45: 
46: # --------------------------------------------------------------------------------
47: def main():
48:     with EchoExampleServer() as app:
49:         app.start()
50: 
51: 
52: # --------------------------------------------------------------------------------
53: if __name__ == '__main__':
54:     try:
55:         main()
56:     except Exception as e:
57:         print(str(e))
58:
```

As with our [previous example](../base.md). We declare our application class and run it.
The only difference here, is the name of our class `EchoExampleServer`.

And there you have it.

A full-blown echo server. With TCP, UDP and UDS communications. In under 60 lines of code!
