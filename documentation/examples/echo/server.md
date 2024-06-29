# The obligatory Echo-server (a.k.a Introducing the endpoint decorator)

---
If you've not looked at the [simplest Ecosystem server](../base.md), you might want to take a look at it. This example expands on that.

The code for this example is located in [examples/echo/echo_example.py](../../../examples/echo/echo_example.py)

To run it, get into your terminal and go to the directory you have cloned this repository into, then:

`python -m examples.echo.echo_example -i 0`

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

---
## The code

As with all frameworks, we will now examine how to get a server to give you back, what you sent in.

Yes, an Ecosystem ... Echo-server.

Here's the code:

```python
 1: import uuid
 2: from pydantic import BaseModel as PydanticBaseModel
 3:                                                                                          
 4: from ecosystem.application_base import ApplicationBase
 5: from ecosystem.configuration import ConfigTCP, ConfigUDP, ConfigUDS
 6: from ecosystem.requests import endpoint
 7:                                                                                          
 8: from .dtos import EchoRequestDto, EchoResponseDto
 9:                                                                                          
10:                                                                                          
11: # --------------------------------------------------------------------------------
12: @endpoint("echo", EchoRequestDto)
13: async def echo_this_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
14:     return EchoResponseDto(message = request.message)
15:                                                                                          
16:                                                                                          
17: # --------------------------------------------------------------------------------
18: class EchoExampleServer(ApplicationBase):
19:     def __init__(self):
20:         self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
21:         self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
22:         self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
23:         super().__init__()
24:                                                                                          
25:                                                                                          
26: # --------------------------------------------------------------------------------
27: def main():
28:     with EchoExampleServer() as app:
29:         app.start()
30:                                                                                          
31:                                                                                          
32: # --------------------------------------------------------------------------------
33: if __name__ == '__main__':
34:     try:
35:         main()
36:     except Exception as e:
37:         print(str(e))
38:
```

### Imports
```python
 1: import uuid
 2: from pydantic import BaseModel as PydanticBaseModel
 3:                                                                                          
 4: from ecosystem.application_base import ApplicationBase
 5: from ecosystem.configuration import ConfigTCP, ConfigUDP, ConfigUDS
 6: from ecosystem.requests import endpoint
 7:                                                                                          
 8: from .dtos import EchoRequestDto, EchoResponseDto
```

1. Line 1 gives us the python `uuid` stuff we'll need with creating an endpoint.
2. Line 2 gives us the Pydantic base model.
   1. Note that I'm importing Pydantic's `BaseModel` class as `PydanticBaseModel`. Strictly speaking this isn't necessary for this example, but it sets a base-line for good development with Ecosystem.
3. Lines 4 and 5 are the same as lines 1 and 2 in our [previous example](../base.md).
4. Line 6 gets us the Ecosystem `endpoint` decorator function.
5. And lastly, we import the two types of Data Transfer Objects (DTOs) we declared for this example.
   1. The DTOs are located in [examples/echo/dtos.py](../../../examples/echo/dtos.py)

### Declaring our Data Transfer Objects (DTOs for short)
Ecosystem uses Pydantic for all it's DTOs.
Here's what you'll see in [examples/echo/dtos.py](../../../examples/echo/dtos.py).
```python
 1: from pydantic import BaseModel as PydanticBaseModel
 2:                                                                                   
 3:                                                                                   
 4: # --------------------------------------------------------------------------------
 5: class EchoRequestDto(PydanticBaseModel):
 6:     message: str
 7:
 8:
 9: # --------------------------------------------------------------------------------
10: class EchoResponseDto(PydanticBaseModel):
11:     message: str
```

As you can see here, we derive our DTOs from our import of Pydantic's `BaseModel` as `PydanticBaseModel`.

Strictly speaking, we could have used the same model for both requests and responses, but this is more complete and demonstrates the purpose of each, more clearly.

Let's get back to the server code then.

### The endpoint decorator
```python
12: @endpoint("echo", EchoRequestDto)
```

Here, on line 12, we use the Ecosystem `endpoint` decorator, to create an endpoint for us.

It expects two things:
1. A route key, in this case `"echo"`
2. A request type, as in the model that a request on this endpoint should honour. In this case, that is `EchoRequestDto`

So, what is a route key?

It is literally nothing more than a string, that gets used in Ecosystem's routing table, to map requests it receives, to your endpoint function.

Just about any string would be valid. If the string can be used as a key in a Python dictionary, and follows the rules of JSON, it's good to go.

So yea, a route key of something arbitrary like `"@@#99asdfaadf"` is completely valid. If you can type it on a keyboard without doing any tricks to get a special character, it will most likely work.

Of course, just because you can do it, does not mean you should. Keep it sane!

IMPORTANT: A route key absolutely must be unique within your application. An Ecosystem application will not even start if you attempt to create two endpoints with the same route key.

### The function
```python
13: async def echo_this_message(request_uuid: uuid.UUID, request) -> PydanticBaseModel:
14:     return EchoResponseDto(message = request.message)
```
On line 13, we declare our endpoint function.

Yes, it must follow that signature.

The parameter list and return type must match.

We'll get to what `request_uuid` is used for in later examples.
Right now, just understand that this function creates an instance of `EchoResponseDto` and returns it.

Of course, the function name may be any valid Python function name.

And yes, it must be an `async def` function. Ecosystem makes liberal use of Python's `asyncio`

Don't freak out if you've not used `asyncio`, or have had trouble using it in the past. Ecosystem abstracts it away for you quite neatly.

# Declaring the application class, and running it.
```python
17: # --------------------------------------------------------------------------------
18: class EchoExampleServer(ApplicationBase):
19:     def __init__(self):
20:         self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
21:         self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
22:         self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
23:         super().__init__()
24:                                                                                          
25:                                                                                          
26: # --------------------------------------------------------------------------------
27: def main():
28:     with EchoExampleServer() as app:
29:         app.start()
30:                                                                                          
31:                                                                                          
32: # --------------------------------------------------------------------------------
33: if __name__ == '__main__':
34:     try:
35:         main()
36:     except Exception as e:
37:         print(str(e))
```

As with our [previous example](../base.md). We declare our application class and run it.
The only difference here, is the name of our class `EchoExampleServer`.

And there you have it.

A full-blown echo server. With TCP, UDP and UDS communications. In under 40 lines of code!

Now ... Let's move on and look at the [client](./client.md).
