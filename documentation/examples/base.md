# The simplest Ecosystem server

---
The code for this example is located in [examples/base/base_example.py](../../examples/base/base_example.py)

To run it, get into your terminal and go to the directory you have cloned this repository into, then:

`python -m examples.base.base_example -i 0`

You should see output similar to this:

```
{"timestamp":"2026-06-19T20:28:05.189040+00:00","severity_number":5,"severity_text":"DEBUG","body":"Using selector: EpollSelector","attributes":{"application_name":"base_example","application_instance":"0","filename":"selector_events.py","lineno":64,"module":"selector_events","funcName":"__init__"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.189567+00:00","severity_number":9,"severity_text":"INFO","body":"Starting stats gathering.","attributes":{"application_name":"base_example","application_instance":"0","filename":"statistics_keeper.py","lineno":135,"module":"statistics_keeper","funcName":"__aenter__"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.189706+00:00","severity_number":9,"severity_text":"INFO","body":"Setting up TCP server.","attributes":{"application_name":"base_example","application_instance":"0","filename":"tcp.py","lineno":19,"module":"tcp","funcName":"__aenter__"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.189821+00:00","severity_number":9,"severity_text":"INFO","body":"Setting up UDP server.","attributes":{"application_name":"base_example","application_instance":"0","filename":"udp.py","lineno":55,"module":"udp","funcName":"__aenter__"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.189909+00:00","severity_number":9,"severity_text":"INFO","body":"Serving UDP on [127.0.0.1:8889]","attributes":{"application_name":"base_example","application_instance":"0","filename":"udp.py","lineno":74,"module":"udp","funcName":"__create_datagram_listener"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.190082+00:00","severity_number":9,"severity_text":"INFO","body":"Setting up UDS server.","attributes":{"application_name":"base_example","application_instance":"0","filename":"uds.py","lineno":21,"module":"uds","funcName":"__aenter__"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.190327+00:00","severity_number":9,"severity_text":"INFO","body":"Serving UDS on /tmp/base_example_0.uds.sock","attributes":{"application_name":"base_example","application_instance":"0","filename":"uds.py","lineno":46,"module":"uds","funcName":"__setup_server"},"trace_id":null,"span_id":null}
{"timestamp":"2026-06-19T20:28:05.190554+00:00","severity_number":9,"severity_text":"INFO","body":"Serving TCP on ('127.0.0.1', 8888)","attributes":{"application_name":"base_example","application_instance":"0","filename":"tcp.py","lineno":41,"module":"tcp","funcName":"__setup_server"},"trace_id":null,"span_id":null}
```

Believe it or not, that is a complete application that will do TCP, UDP and UDS communications.

On Linux you can execute a `netcat` command and test it right now.

For TCP:
```shell
echo '{"span_key": {"trace_id": "12345678-1234-1234-1234-1234567890ab", "span_id": "1234567890abcdef"}, "route_key": "eco.statistics.get", "data": {"type": "current"}}' | nc localhost 8888
```

For UDP:
```shell
echo '{"span_key": {"trace_id": "12345678-1234-1234-1234-1234567890ab", "span_id": "1234567890abcdef"}, "route_key": "eco.statistics.get", "data": {"type": "current"}}' | nc -u localhost 8889
```

For UDS:
```shell
echo '{"span_key": {"trace_id": "12345678-1234-1234-1234-1234567890ab", "span_id": "1234567890abcdef"}, "route_key": "eco.statistics.get", "data": {"type": "current"}}' | nc -U /tmp/base_example_0.uds.sock
```

In all three cases, you'll get a response similar to:

```json
{"span_key":{"trace_id":"12345678-1234-1234-1234-1234567890ab","span_id":"1234567890abcdef"},"status":0,"data":{"statistics":{"endpoint_data":{"eco":{"log":{"level":{"call_count":0,"p95":-1.0,"p99":-1.0},"buffer":{"call_count":0,"p95":-1.0,"p99":-1.0}},"statistics":{"get":{"call_count":5,"p95":0.0007168467536757817,"p99":0.0007237349544084281}},"error_states":{"get":{"call_count":0,"p95":-1.0,"p99":-1.0},"clear":{"call_count":0,"p95":-1.0,"p99":-1.0}},"buffered_handler":{"data":{"call_count":0,"p95":-1.0,"p99":-1.0},"receiving":{"pause":{"call_count":0,"p95":-1.0,"p99":-1.0},"unpause":{"call_count":0,"p95":-1.0,"p99":-1.0}},"processing":{"pause":{"call_count":0,"p95":-1.0,"p99":-1.0},"unpause":{"call_count":0,"p95":-1.0,"p99":-1.0}},"all":{"pause":{"call_count":0,"p95":-1.0,"p99":-1.0},"unpause":{"call_count":0,"p95":-1.0,"p99":-1.0}},"errors":{"get_first_10":{"call_count":0,"p95":-1.0,"p99":-1.0},"reprocess":{"all":{"call_count":0,"p95":-1.0,"p99":-1.0},"one":{"call_count":0,"p95":-1.0,"p99":-1.0}},"clear":{"call_count":0,"p95":-1.0,"p99":-1.0},"pop_request":{"call_count":0,"p95":-1.0,"p99":-1.0},"inspect_request":{"call_count":0,"p95":-1.0,"p99":-1.0}}},"buffered_sender":{"data":{"call_count":0,"p95":-1.0,"p99":-1.0},"send_process":{"pause":{"call_count":0,"p95":-1.0,"p99":-1.0},"unpause":{"call_count":0,"p95":-1.0,"p99":-1.0}},"errors":{"get_first_10":{"call_count":0,"p95":-1.0,"p99":-1.0},"reprocess":{"all":{"call_count":0,"p95":-1.0,"p99":-1.0},"one":{"call_count":0,"p95":-1.0,"p99":-1.0}},"clear":{"call_count":0,"p95":-1.0,"p99":-1.0},"pop_request":{"call_count":0,"p95":-1.0,"p99":-1.0},"inspect_request":{"call_count":0,"p95":-1.0,"p99":-1.0}}}}},"timestamp":1781710188.1312137,"uptime":501.13121366500854,"gather_period":300,"application":{"name":"base_example","instance":"0"}}}}
```

By the time that is run through something that makes the JSON more readable, it looks this:
```json
{
   "data" : {
      "statistics" : {
         "application" : {"instance" : "0", "name" : "base_example"},
         "endpoint_data" : {
            "eco" : {
               "buffered_handler" : {
                  "all" : {
                     "pause"  : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "unpause": {"call_count" : 0, "p95" : -1, "p99" : -1}
                  },
                  "data" : {"call_count" : 0, "p95" : -1, "p99" : -1},
                  "errors" : {
                     "clear"          : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "get_first_10"   : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "inspect_request": {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "pop_request"    : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "reprocess"      : {
                        "all": {"call_count" : 0, "p95" : -1, "p99" : -1},
                        "one": {"call_count" : 0, "p95" : -1, "p99" : -1}
                     }
                  },
                  "processing" : {
                     "pause"  : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "unpause": {"call_count" : 0, "p95" : -1, "p99" : -1}
                  },
                  "receiving" : {
                     "pause"  : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "unpause": {"call_count" : 0, "p95" : -1, "p99" : -1}
                  }
               },
               "buffered_sender" : {
                  "data" : {"call_count" : 0, "p95" : -1, "p99" : -1},
                  "errors" : {
                     "clear"          : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "get_first_10"   : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "inspect_request": {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "pop_request"    : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "reprocess"      : {
                        "all" : {"call_count" : 0, "p95" : -1, "p99" : -1},
                        "one" : {"call_count" : 0, "p95" : -1, "p99" : -1}
                     }
                  },
                  "send_process" : {
                     "pause"  : {"call_count" : 0, "p95" : -1, "p99" : -1},
                     "unpause": {"call_count" : 0, "p95" : -1, "p99" : -1}
                  }
               },
               "error_states" : {
                  "clear": {"call_count" : 0, "p95" : -1, "p99" : -1},
                  "get"  : {"call_count" : 0, "p95" : -1, "p99" : -1}
               },
               "log" : {
                  "buffer": {"call_count" : 0, "p95" : -1, "p99" : -1},
                  "level" : {"call_count" : 0, "p95" : -1, "p99" : -1}
               },
               "statistics" : {
                  "get" : {"call_count" : 5, "p95" : 0.000716846753675782, "p99" : 0.000723734954408428}
               }
            }
         },
         "gather_period" : 300,
         "timestamp" : 1781710188.13121,
         "uptime" : 501.131213665009
      }
   },
   "span_key" : {
      "span_id" : "1234567890abcdef",
      "trace_id" : "12345678-1234-1234-1234-1234567890ab"
   },
   "status" : 0
}
```

That's rather cool, but let's get into the code and see what we are doing here.

---
## The code

A complete Ecosystem server, though not a very useful one, can be written in under 30 lines of code. Less, if you don't care about code readability.

Here it is:

```python
 1: from ekosis.application_base import ApplicationBase
 2: from ekosis.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS
 3: 
 4: 
 5: # --------------------------------------------------------------------------------
 6: class BaseExampleServer(ApplicationBase):
 7:     def __init__(self):
 8:         self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
 9:         self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
10:         self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
11:         super().__init__()
12: 
13: 
14: # --------------------------------------------------------------------------------
15: def main():
16:     with BaseExampleServer() as app:
17:         app.start()
18: 
19: 
20: # --------------------------------------------------------------------------------
21: if __name__ == '__main__':
22:     try:
23:         main()
24:     except Exception as e:
25:         print(str(e))
26:
```

---
### Imports
On line 1 and 2 we import the stuff we'll need from Ecosystem.

```python
 1: from ekosis.application_base import ApplicationBase
 2: from ekosis.configuration.config_models import ConfigTCP, ConfigUDP, ConfigUDS
```

- `ApplicationBase` is the class from which we will derive our application's class,
- `ConfigTCP`, `ConfigUDP` and `ConfigUDS` are used to configure the various servers the application will be running.

---
### Getting it ready to run
```python
 6: class BaseExampleServer(ApplicationBase):
 7:     def __init__(self):
 8:         self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8888)
 9:         self._configuration.udp = ConfigUDP(host="127.0.0.1", port=8889)
10:         self._configuration.uds = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT")
11:         super().__init__()
```
On line 6 we start declaration and definition of our application. We derive a class `BaseExampleServer`, from Ecosystem's `ApplicationBase` class.

Then we proceed to do a bit of configuration in the `__init__` method of `BaseExampleServer`

On lines 8, 9 and 10, we are configuring the TCP, UDP and UDS servers that we want.

Line 11 does the call to the `ApplicationBase` `__init__` method.

Note, this is **not** how an Ecosystem application should be configured.
What you are seeing here, is purely for example purposes.

There are in fact, three ways in which you can configure an Ecosystem application.

1. The way you are seeing here, using programmatic intervention before calling the `ApplicationBase` `__init__` method.
2. Through the use of a JSON file, containing the same information.
3. Using environment variables.

You'll use option `2` for your local development environment.
Option `3` is for production environments.

We'll get to the details of `2` and `3` above. Right now though, just look at the code. I'm quite certain you'll understand, that we are creating an application contained in a file named `base_example.py`

!!! THIS IS IMPORTANT !!!
1. Ecosystem uses `sys.argv[0]` as your application's name. This means that the name of the python file that you specify when running your application, provides Ecosystem with the name of your application!
2. The `.py` extension of the file name gets stripped, leaving only the base name of the file.
3. In this case, it means that our application's name is: `base_example`
4. Keep this in mind! It will become very, very important when you start using Ecosystem for its true purpose.

Another thing to note here:

If you do not set the configuration for a server type, your application will not even start that server.
So yes, you can have an Ecosystem application that has any combination of TCP, UDP or UDS servers, including none at all. Though that won't be very useful now, would it?

---
# Running it.
From line 15 to 25, we declare a function called `main`, and then we proceed to run it.
```python
14: # --------------------------------------------------------------------------------
15: def main():
16:     with BaseExampleServer() as app:
17:         app.start()
18:                                                                                          
19:                                                                                          
20: # --------------------------------------------------------------------------------
21: if __name__ == '__main__':
22:     try:
23:         main()
24:     except Exception as e:
25:         print(str(e))
```

That is it. All of it.

Once you are comfortable with this example, take a look at an Ecosystem [Echo-server](echo/server.md).
