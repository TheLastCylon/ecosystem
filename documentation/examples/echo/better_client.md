# A better Echo-client (a.k.a Introducing the sender decorator)

In our previous [Echo-client example](./client.md), our `tcp_send`, `udp_send` and `uds_send` methods, used the `send_message` method of the various clients, directly.

In a simple example like an Echo-client, this approach is good enough. But things are never this easy in the real world!

When you start dealing with more complex requirements, doing things the way we did in the previous example, will become tedious and bug ridden very quickly.

So, allow me to show you a better way.

The code you are about to see, does exactly the same as the previous example. Only in a more maintainable way.

You can run it with: `python -m examples.echo.better_client`

Remember to have the Echo-server up and running with: `python -m examples.echo.server -i 0`

## The Code
```python
 1: import asyncio
 2: 
 3: from ecosystem.clients import TCPClient, UDPClient, UDSClient
 4: from ecosystem.sending import sender
 5: 
 6: from .server import EchoRequestDto, EchoResponseDto
 7: 
 8: client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
 9: client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
10: client_uds = UDSClient("/tmp/echo_example_0_uds.sock")
11: 
12: 
13: # --------------------------------------------------------------------------------
14: def make_echo_request_dto(message: str) -> EchoRequestDto:
15:     return EchoRequestDto(message=message)
16: 
17: 
18: # --------------------------------------------------------------------------------
19: @sender(client_tcp, "echo", EchoResponseDto)
20: async def tcp_send(message: str):
21:     return make_echo_request_dto(message)
22: 
23: 
24: # --------------------------------------------------------------------------------
25: @sender(client_udp, "echo", EchoResponseDto)
26: async def udp_send(message: str):
27:     return make_echo_request_dto(message)
28: 
29: 
30: # --------------------------------------------------------------------------------
31: @sender(client_uds, "echo", EchoResponseDto)
32: async def uds_send(message: str):
33:     return make_echo_request_dto(message)
34: 
35: 
36: # --------------------------------------------------------------------------------
37: async def send_message(message):
38:     print("========================================")
39:     print(f"Sending message on TCP: [{message}]")
40:     response = await tcp_send(message)
41:     print(f"TCP Response          : [{response.message}]")
42:     print("----------------------------------------")
43:     print(f"Sending message on UDP: [{message}]")
44:     response = await udp_send(message)
45:     print(f"UDP Response          : [{response.message}]")
46:     print("----------------------------------------")
47:     print(f"Sending message on UDS: [{message}]")
48:     response = await uds_send(message)
49:     print(f"UDS Response          : [{response.message}]")
50:     print("========================================")
51: 
52: 
53: # --------------------------------------------------------------------------------
54: async def main():
55:     try:
56:         message: str = input('Enter message: ')
57:         while message != "quit":
58:             await send_message(message)
59:             message = input('Enter message: ')
60:         print("Bye!")
61:     except Exception as e:
62:         print(str(e))
63:         return
64: 
65: # --------------------------------------------------------------------------------
66: asyncio.run(main())
67:
```

### Imports
```python
 1: import asyncio
 2: 
 3: from ecosystem.clients import TCPClient, UDPClient, UDSClient
 4: from ecosystem.sending import sender
 5: 
 6: from .server import EchoRequestDto, EchoResponseDto
 7: 
```

This is very similar to the imports from the previous example.
Two things are different though:
1. We do not import anything from `typing`
2. We import the Ecosystem `sender` decorator on line 4.

Yes, we are still importing the DTOs directly from the server code, I promise we'll stop doing that kind of thing soon.

### Instantiating the clients
```python
 8: client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
 9: client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
10: client_uds = UDSClient("/tmp/echo_example_0_uds.sock")
```

Exactly as before, we instantiate our clients.

### The request DTO maker function:
```python
14: def make_echo_request_dto(message: str) -> EchoRequestDto:
15:     return EchoRequestDto(message=message)
```

This is just a function that knows how to take data we pass into it, and create the response DTO we need from it.

### The sender functions, decorated with the Ecosystem sender decorator
```python
18: # --------------------------------------------------------------------------------
19: @sender(client_tcp, "echo", EchoResponseDto)
20: async def tcp_send(message: str):
21:     return make_echo_request_dto(message)
22: 
23: 
24: # --------------------------------------------------------------------------------
25: @sender(client_udp, "echo", EchoResponseDto)
26: async def udp_send(message: str):
27:     return make_echo_request_dto(message)
28: 
29: 
30: # --------------------------------------------------------------------------------
31: @sender(client_uds, "echo", EchoResponseDto)
32: async def uds_send(message: str):
33:     return make_echo_request_dto(message)
```

Here you see me creating the `tcp_send`, `udp_send` and `uds_send` functions again.
The major difference here is, the `sender` decorator is doing a lot of heavy lifting for us.

The `sender` decorator needs four things:
1. An instantiated client that the message will be sent on.
2. The route key that the server is listening on for requests of the type you are wanting to send.
3. The response DTO type you expect from the server.
4. A function that returns an instantiated request DTO, that you want to send.

If you are paying attention you'll note that, with this approach, all we'll have to maintain in the future is:
1. The request DTO
2. The response DTO
3. How to create a request DTO from data we have at hand. i.e. The `make_echo_request_dto` function.

### The rest of it
```python
36: # --------------------------------------------------------------------------------
37: async def send_message(message):
38:     print("========================================")
39:     print(f"Sending message on TCP: [{message}]")
40:     response = await tcp_send(message)
41:     print(f"TCP Response          : [{response.message}]")
42:     print("----------------------------------------")
43:     print(f"Sending message on UDP: [{message}]")
44:     response = await udp_send(message)
45:     print(f"UDP Response          : [{response.message}]")
46:     print("----------------------------------------")
47:     print(f"Sending message on UDS: [{message}]")
48:     response = await uds_send(message)
49:     print(f"UDS Response          : [{response.message}]")
50:     print("========================================")
51: 
52: 
53: # --------------------------------------------------------------------------------
54: async def main():
55:     try:
56:         message: str = input('Enter message: ')
57:         while message != "quit":
58:             await send_message(message)
59:             message = input('Enter message: ')
60:         print("Bye!")
61:     except Exception as e:
62:         print(str(e))
63:         return
64: 
65: # --------------------------------------------------------------------------------
66: asyncio.run(main())
```

Is exactly the same as our previous example.

# A note on the sender decorator
For those of you who are deeper into Python's guts than most, and feel ready to scream at me:

Yes, you are absolutely right!

I am slightly abusing Python's decorators with the `sender` decorator.

1. I am fully aware that decorators are intended to add functionality to a function, rather than altering a function's signature, in the way I do with `sender`.
2. I'm also fully aware that the only reason IDEs and every linting tool out there, isn't complaining about this example, is that 
`EchoRequestDto` and `EchoResponseDto` have identical members.

In this case though, I feel it is 100% justified.

1. The solution follows the DRY principal and reduces the amount of code that needs to be written and maintained too near nothing.
2. There is no runtime problem in doing this! And in terms of documentation, hardly any is needed. Both the return and response type are contained within the function decoration and declaration.
3. I'm also quite certain the various IDEs, linting tools and Python's type hinting system will catch up ... Eventually.
