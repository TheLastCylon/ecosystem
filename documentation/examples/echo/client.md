# And now, the Echo-client

We've seen how to create an [Echo-server](./server.md) with Ecosystem, now let's take a look at making an Echo-client.

In order to test this client, get into your terminal and go to the directory you have cloned this repository into, then:

1. Start the [Echo-server](./server.md) with: `python -m examples.echo.echo_example -i 0`
2. Get into another terminal and start the Echo-client with: `python -m examples.echo.client`

You should see a prompt like this:
```
Enter message:
```

Enter a message and get a response. If you enter `This is a test` you'll see:

```
Enter message: This is a test
========================================
Sending message on TCP: [This is a test]
TCP Response          : [This is a test]
----------------------------------------
Sending message on UDP: [This is a test]
UDP Response          : [This is a test]
----------------------------------------
Sending message on UDS: [This is a test]
UDS Response          : [This is a test]
========================================
Enter message: 
```

In order to stop the client, just enter `quit` at the prompt.

Now, let's jump into it.

## The code:
You can find this code in [examples/echo/client.py](../../../examples/echo/client.py)

```python
 1: import asyncio
 2: 
 3: from typing import cast
 4: 
 5: from ecosystem.clients import TCPClient, UDPClient, UDSClient
 6: 
 7: from .dtos import EchoRequestDto, EchoResponseDto
 8: 
 9: client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
10: client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
11: client_uds = UDSClient("/tmp/echo_example_0_uds.sock")
12: 
13: 
14: # --------------------------------------------------------------------------------
15: async def tcp_send(message):
16:     response = await client_tcp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
17:     return cast(EchoResponseDto, response)
18: 
19: 
20: # --------------------------------------------------------------------------------
21: async def udp_send(message):
22:     response = await client_udp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
23:     return cast(EchoResponseDto, response)
24: 
25: 
26: # --------------------------------------------------------------------------------
27: async def uds_send(message):
28:     response = await client_uds.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
29:     return cast(EchoResponseDto, response)
30: 
31: 
32: # --------------------------------------------------------------------------------
33: async def send_message(message):
34:     print("========================================")
35:     print(f"Sending message on TCP: [{message}]")
36:     response = await tcp_send(message)
37:     print(f"TCP Response          : [{response.message}]")
38:     print("----------------------------------------")
39:     print(f"Sending message on UDP: [{message}]")
40:     response = await udp_send(message)
41:     print(f"UDP Response          : [{response.message}]")
42:     print("----------------------------------------")
43:     print(f"Sending message on UDS: [{message}]")
44:     response = await uds_send(message)
45:     print(f"UDS Response          : [{response.message}]")
46:     print("========================================")
47: 
48: 
49: # --------------------------------------------------------------------------------
50: async def main():
51:     try:
52:         message: str = input('Enter message: ')
53:         while message != "quit":
54:             await send_message(message)
55:             message = input('Enter message: ')
56:         print("Bye!")
57:     except Exception as e:
58:         print(str(e))
59:         return
60: 
61: # --------------------------------------------------------------------------------
62: asyncio.run(main())
63:
```

### Imports
From line 1 to 7 we are just doing imports.
```python
 1: import asyncio
 2: 
 3: from typing import cast
 4: 
 5: from ecosystem.clients import TCPClient, UDPClient, UDSClient
 6: 
 7: from .dtos import EchoRequestDto, EchoResponseDto
```

We import `asyncio` on line 1. Again: Don't freak out if you've never used `asyncio` or find it hard to understand. Ecosystem abstracts most of that away for you.

On line 3 we import `cast` from `typing`, this isn't strictly necessary, but it does make for good coding practice when we want our type hinting in our IDEs to work properly.

Line 5 is where we get the TCP, UDP and UDS client classes from Ecosystem.

And on lines 7, we grab the request and response DTOs we created in [examples/echo/dtos.py](../../../examples/echo/dtos.py).

### Instantiating the clients
```python
 9: client_tcp = TCPClient(server_host='127.0.0.1', server_port=8888)
10: client_udp = UDPClient(server_host='127.0.0.1', server_port=8889)
11: client_uds = UDSClient("/tmp/echo_example_0_uds.sock")
```

From lines 9 to 11, we instantiate each of our clients classes.
I'm sure you can see the TCP and UDP clients will be connecting to a host on `127.0.0.1` for ports `8888` and `8889` respectively.

It is with the UDS client that things might look wonky.

Keep in mind that, in the server, we configured the UDS client to use a `socket_file_name` of `"DEFAULT"`.
This causes Ecosystem to construct a socket file name, consisting out of your application name and its instance id.

In the case of our Echo-server then, the socket file name is: `echo_example` + `0` + `_uds.sock`

**VERY, VERY IMPORTANT!!**

If you don't use `"DEFAULT"` in your UDS server configurations, it is up to you to make sure you either only run one instance of your application on any given machine, or you somehow keep the names unique, between your various running instances.

### Some neatly laid out send functions
```python
14: # --------------------------------------------------------------------------------
15: async def tcp_send(message):
16:     response = await client_tcp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
17:     return cast(EchoResponseDto, response)
18: 
19: 
20: # --------------------------------------------------------------------------------
21: async def udp_send(message):
22:     response = await client_udp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
23:     return cast(EchoResponseDto, response)
24: 
25: 
26: # --------------------------------------------------------------------------------
27: async def uds_send(message):
28:     response = await client_udp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
29:     return cast(EchoResponseDto, response)
```

Here you see send functions for TCP, UDP and UDS respectively.
They all do the same thing, and the `send_message` method for each of the clients all have the same interface.

So let's take a look at `send_message` in our `tcp_send` function:
```python
15: async def tcp_send(message):
16:     response = await client_tcp.send_message("echo", EchoRequestDto(message = message), EchoResponseDto)
17:     return cast(EchoResponseDto, response)
```

On line 16, the `send_message` method of `client_tcp`, expects three things from you:
1. A route key, in this case: `"echo"`
2. Data to send in the form of a DTO.
   1. In this case we take the message string that the `tcp_send` function receives, and put it inside an instance of `EchoRequestDto`.
3. A response type DTO. In this case, our `EchoResponseDto`

This whole thing with the DTOs, is so that everything is neatly validated by Pydantic. Without it, we'd have to deal with raw JSON and write validation for it ourselves.

On line 17, we take the `response` from `send_message`, and cast it to our `EchoResponseDto`.

Again, not strictly needed, but good practice and helps keep our type hinting stuff working nicely.

The other two functions, `udp_send` and `uds_send`, do exactly the same, just for each of the other two clients.

So let's move on.

### Do it in triplicate
```python
32: # --------------------------------------------------------------------------------
33: async def send_message(message):
34:     print("========================================")
35:     print(f"Sending message on TCP: [{message}]")
36:     response = await tcp_send(message)
37:     print(f"TCP Response          : [{response.message}]")
38:     print("----------------------------------------")
39:     print(f"Sending message on UDP: [{message}]")
40:     response = await udp_send(message)
41:     print(f"UDP Response          : [{response.message}]")
42:     print("----------------------------------------")
43:     print(f"Sending message on UDS: [{message}]")
44:     response = await uds_send(message)
45:     print(f"UDS Response          : [{response.message}]")
46:     print("========================================")
```

From line 33 to 46, we declare a function that does nothing more than call each of the `tcp_send`, `udp_send` and `uds_send` functions in turn.
Along with some nice output, so we can see what's going on in the terminal.

### And then we loop it
```python
49: # --------------------------------------------------------------------------------
50: async def main():
51:     try:
52:         message: str = input('Enter message: ')
53:         while message != "quit":
54:             await send_message(message)
55:             message = input('Enter message: ')
56:         print("Bye!")
57:     except Exception as e:
58:         print(str(e))
59:         return
60: 
61: # --------------------------------------------------------------------------------
62: asyncio.run(main())
```

Yea, the `main` function here is nothing more than a loop that accepts our input and passes it to where we send it.

On line 62 we call the `main` function with `asyncio.run(main())`.

## Conclusion
At this point you have a solid grip on what goes into making a client with Ecosystem.

Thing is, in terms of maintainability, this won't cut it in the real world. So, [let's take a look at how to do it better](./better_client.md).
