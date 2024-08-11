# HTTP Client example

Ecosystem's `sender` decorator and clients, function seamlessly with
[FastAPI](https://github.com/fastapi/fastapi).

The combination of Ecosystem with FastAPI, is quite powerful, and effectively
negates the need for HTTP in distributed systems. Allowing one to have all the
tools and utility of existing HTTP technologies, while taking advantage of the
communication speeds gained from using UDP.

I'm quite certain that anyone making it to this point in the examples, will
understand that:

1. Having a distributed system, and
2. a web-server capable of being a client to that system,
3. using a protocol that is NOT HTTP ...
4. **Has significant advantages.**

What's more though, is the fact that between Ecosystem and FastAPI, this
is achieved with hardly any code at all.

## The example
To run this example, you will need [FastAPI](https://github.com/fastapi/fastapi)
installed. Please refer to their documentation for that.

Then, to run the example:
1. Start up the [Echo server](../echo/server.md) example with
   `python -m examples.echo.echo_example -i 0` from the directory you cloned
   this repository into.
2. Start the HTTP client example with
   `fastapi dev examples/http_client_example/main.py`.

Now you can use either `curl` or the local
[FastAPI docs url](http://127.0.0.1:8000/docs) from your browser, to
make a call to the FastAPI application, which in turn makes a call to the
Ecosystem Echo example server.

### Example curl command
```shell
curl -X POST 'http://127.0.0.1:8000/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "My Test Message."
}'
```

### The code
When you examine the code in
[`main.py`](../../../examples/http_client_example/main.py) of the `http_example`
code. You'll see:

```python
 1: from fastapi import FastAPI
 2: 
 3: from ekosis.clients import UDPClient
 4: from ekosis.sending.sender import sender
 5: 
 6: from dtos import EchoRequestDto, EchoResponseDto
 7: 
 8: test_client = UDPClient("127.0.0.1", 8889)
 9: 
10: @sender(test_client, "echo", EchoResponseDto)
11: async def echo_endpoint(message: str, **kwargs):
12:     return EchoRequestDto(message=message)
13: 
14: app = FastAPI()
15: 
16: @app.post("/")
17: async def root(dto: EchoRequestDto):
18:     return await echo_endpoint(dto.message)
```

The FastAPI part of this is beyond the scope of this documentation. But I'm
certain you'll notice that, with less than 20 lines of code, we:

1. Created an HTTP server with an endpoint, that accepts a text message.
2. Passes the received message to an Ecosystem server, using a UDP client.
3. Gets a response from that server.
4. Provides that response to the calling browser/curl command.

Also note that in this example uses the exact same code for, `EchoRequestDto`
and `EchoResponseDto`, provide in the Ecosystem [Echo server](../echo/server.md)
example.

This means: Yes, you can use the DTOs for your Ecosystem applications, directly
in [FastAPI](https://github.com/fastapi/fastapi) applications.

No need for any kind of tricks or extra code. Use them as is.

Combine this with all the features provided by Ecosystem as a framework, and
every single aspect of distributed systems, is solved.

If you're not convinced, imagine having a web-server capable of being a client
to the [Proper Fun Example system](../proper_fun.md).

Also try to understand, that the web-server would be able to be a client to
any of the components in that system.

Again: The combination of Ecosystem and FastAPI, makes for a tech-stack that
solves problems at all levels of developing the Software Development Life
Cycle for distributed systems.

Personally, I've not seen another tech-stack delivering so much, with so little
effort.
