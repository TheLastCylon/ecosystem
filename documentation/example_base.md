# The simplest Ecosystem server

The code for this example is located in [examples/base/server.py](../examples/base/server.py)

To run it, get into your terminal and go to the directory you have cloned this repository into, then:

`python -m examples.base.server`

You should see output similar to this:

```
20240619122301.385|base_example-0|INFO|statistics_keeper.py|82|Starting stats gathering.
20240619122301.385|base_example-0|INFO|tcp.py|25|Setting up TCP server.
20240619122301.385|base_example-0|INFO|udp.py|28|Setting up UDP server.
20240619122301.385|base_example-0|INFO|uds.py|28|Setting up UDS server.
20240619122301.386|base_example-0|INFO|udp.py|58|Serving UDP on [127.0.0.1:8889]
20240619122301.386|base_example-0|INFO|uds.py|48|Serving UDS on /tmp/base_example_0_uds.sock
20240619122301.386|base_example-0|INFO|tcp.py|42|Serving TCP on ('127.0.0.1', 8888)
```

## Let's jump right into it

A complete Ecosystem server, though not a very useful one, can be written in 27 lines of code. Less, if you don't care about code readability.

Here it is:

```python
 1: from ecosystem import ApplicationBase, TCPConfig, UDPConfig, UDSConfig
 2: 
 3: 
 4: # --------------------------------------------------------------------------------
 5: class BaseServer(ApplicationBase):
 6:     def __init__(self):
 7:         super().__init__(
 8:                 "base_example",               # A unique name for your application
 9:                 "0",                          # The instance for this application.
10:                 [],                           # Don't worry about this right now, we'll get to it later
11:                 TCPConfig("127.0.0.1", 8888), # The TCP configuration
12:                 UDPConfig("127.0.0.1", 8889), # The UDP configuration
13:                 UDSConfig("/tmp"),            # The UDS configuration
14:                 '/tmp'                        # The directory in which you want log files to be written.
15:         )
16: 
17: 
18: # --------------------------------------------------------------------------------
19: def main():
20:     app = BaseServer()
21:     app.start()
22: 
23: 
24: # --------------------------------------------------------------------------------
25: if __name__ == '__main__':
26:     main()
```

Believe it or not, that is a complete application that will do TCP, UDP and UDS communications.

On Linux you can execute a `netcat` command and test it right now.

For TCP:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "eco-statistics", "data": {"type": "current"}}' | nc localhost 8888
```

For UDP:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "eco-statistics", "data": {"type": "current"}}' | nc -u localhost 8889
```

For UDS:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "eco-statistics", "data": {"type": "current"}}' | nc -U /tmp/base_example_0_uds.sock
```

In all three cases, you'll get a response similar to:

```json
{"uid":"abcdef01-abcd-abcd-abcd-abcdef012345","status":0,"data":{"statistics":{"uptime":1773,"handlers":{"eco-statistics":{"calls":4}}}}}
```

That's rather cool, but let's get into the code and see what we are doing here.

First things first: Line number 1.

We import the stuff we need from Ecosystem:
```python
 1: from ecosystem import ApplicationBase, TCPConfig, UDPConfig, UDSConfig
```

- `ApplicationBase` is the class from which we will derive our application,
- `TCPConfig, UDPConfig, UDSConfig` are classes used to configure each of server types.

At this point it's worth noting that if you pass `None` for any one of these configurations, that type of server will not be available in your application. It won't even start.
So yes, you can have an Ecosystem application that has any combination of TCP, UDP or UDS servers, including none at all. Though that won't be very useful now, would it?