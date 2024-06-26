# The simplest Ecosystem server

The code for this example is located in [examples/base/server.py](../examples/base/server.py)

To run it, get into your terminal and go to the directory you have cloned this repository into, then:

`python -m examples.base.server -i 0`

You should see output similar to this:

```
20240620025650.578|base_example-0|INFO|statistics_keeper.py|82|Starting stats gathering.
20240620025650.579|base_example-0|INFO|tcp.py|26|Setting up TCP server.
20240620025650.579|base_example-0|INFO|udp.py|28|Setting up UDP server.
20240620025650.579|base_example-0|INFO|uds.py|28|Setting up UDS server.
20240620025650.579|base_example-0|INFO|udp.py|58|Serving UDP on [127.0.0.1:8889]
20240620025650.579|base_example-0|INFO|uds.py|48|Serving UDS on /tmp/base_example-0_uds.sock
20240620025650.579|base_example-0|INFO|tcp.py|43|Serving TCP on ('127.0.0.1', 8888)
```
Believe it or not, that is a complete application that will do TCP, UDP and UDS communications.

On Linux you can execute a `netcat` command and test it right now.

For TCP:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "eco.statistics.get", "data": {"type": "current"}}' | nc localhost 8888
```

For UDP:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "eco.statistics.get", "data": {"type": "current"}}' | nc -u localhost 8889
```

For UDS:
```shell
echo '{"uid": "abcdef01-abcd-abcd-abcd-abcdef012345", "route_key": "eco.statistics.get", "data": {"type": "current"}}' | nc -U /tmp/base_example_0_uds.sock
```

In all three cases, you'll get a response similar to:

```json
{"uid":"abcdef01-abcd-abcd-abcd-abcdef012345","status":0,"data":{"statistics":{"uptime":1773,"handlers":{"eco-statistics":{"calls":4}}}}}
```

That's rather cool, but let's get into the code and see what we are doing here.

## The code

A complete Ecosystem server, though not a very useful one, can be written in under 40 lines of code. Less, if you don't care about code readability.

Here it is:

```python
 1: from ecosystem import ApplicationBase
 2: from ecosystem import ConfigApplication
 3: from ecosystem import ConfigApplicationInstance
 4: from ecosystem import ConfigTCP
 5: from ecosystem import ConfigUDP
 6: from ecosystem import ConfigUDS
 7: 
 8: app_config          = ConfigApplication(name = "base_example")
 9: app_instance_config = ConfigApplicationInstance(
10:     instance_id = "0",
11:     tcp         = ConfigTCP(host="127.0.0.1", port=8888),
12:     udp         = ConfigUDP(host="127.0.0.1", port=8889),
13:     uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
14: )
15: app_config.instances[app_instance_config.instance_id] = app_instance_config
16: 
17: 
18: # --------------------------------------------------------------------------------
19: class BaseExampleServer(ApplicationBase):
20:     def __init__(self):
21:         super().__init__(app_config.name, app_config)
22: 
23: 
24: # --------------------------------------------------------------------------------
25: def main():
26:     with BaseExampleServer() as app:
27:         app.start()
28: 
29: 
30: # --------------------------------------------------------------------------------
31: if __name__ == '__main__':
32:     try:
33:         main()
34:     except Exception as e:
35:         print(str(e))
36:
```

### Imports
From line 1 to 6 we import the stuff we'll need from Ecosystem.

```python
 1: from ecosystem import ApplicationBase
 2: from ecosystem import ConfigApplication
 3: from ecosystem import ConfigApplicationInstance
 4: from ecosystem import ConfigTCP
 5: from ecosystem import ConfigUDP
 6: from ecosystem import ConfigUDS
```

- `ApplicationBase` is the class from which we will derive our application's class,
- `ConfigApplication` is used to contain instance level configurations for your applications.
- `ConfigApplicationInstance` is used to configure a specific instance of your application.
- And of course: `ConfigTCP`, `ConfigUDP` and `ConfigUDS` are used to configure the various servers your application will be running.

### Configuration
From line 8 to 15, we configure this particular instance of the application.
```python
 8: app_config          = ConfigApplication(name = "base_example")
 9: app_instance_config = ConfigApplicationInstance(
10:     instance_id = "0",
11:     tcp         = ConfigTCP(host="127.0.0.1", port=8888),
12:     udp         = ConfigUDP(host="127.0.0.1", port=8889),
13:     uds         = ConfigUDS(directory="/tmp", socket_file_name="DEFAULT"),
14: )
15: app_config.instances[app_instance_config.instance_id] = app_instance_config
```

At this point it's worth noting that there are three ways in which you can configure an application instance.
1. The way you are seeing here, using a manually instantiated object of type `ConfigApplication`
2. Through the use of a JSON file, containing the same information.
3. Using environment variables.

We'll get to `2` and `3` above, right now just look at the configuration code you see there. I'm quite certain you'll get that:
1. We are creating a configuration for an application named `base_example`
2. Then we create an instance configuration, for a running instance, that we want to call `0`.
3. Then we configure each of our possible servers.
   1. I'm sure you can see the TCP server is going to run for host `127.0.0.1`, and listen on port `8888`.
   2. Similarly, the UDP server will run for host `127.0.0.1`, and listen on port `8889`.
   3. There's a little something that's happening with the UDS port setup though:
      1. First off: Yes! You can set `socket_file_name` to any valid string that can be used on a file system for an OS that supports UDS.
      2. If you set it to `"DEFAULT"` like we do here though, Ecosystem will create a file name that is a combination of:
         1. Your application name
         2. The instance id.
      3. In our example, the file will live in the `/tmp` directory and be named: `base_example_0_uds.sock`. i.e. It's absolute path will be: `/tmp/base_example_0_uds.sock`
4. And finally we add the application-instance configuration, to the application configuration.

I realize that all this business with instance configuration might be freaky for some. Right now, please know that I have damn good reason for doing this.

Another thing to note here:

If you do not set the configuration for a server type, your application will not even start that server.
So yes, you can have an Ecosystem application that has any combination of TCP, UDP or UDS servers, including none at all. Though that won't be very useful now, would it?

# Declaring the application class, and running it.
From line 18 to 35, we declare our class and write the code for getting it running.
```python
18: # --------------------------------------------------------------------------------
19: class BaseExampleServer(ApplicationBase):
20:     def __init__(self):
21:         super().__init__(app_config.name, app_config)
22: 
23: 
24: # --------------------------------------------------------------------------------
25: def main():
26:     with BaseExampleServer() as app:
27:         app.start()
28: 
29: 
30: # --------------------------------------------------------------------------------
31: if __name__ == '__main__':
32:     try:
33:         main()
34:     except Exception as e:
35:         print(str(e))
36:
```

I'm certain you've seen this pattern before.

1. We declare our application class as `BaseExampleServer` and then pass all the required values to the `ApplicationBase` class.
2. We instantiate our class in the `main` function on line 26, within a Python context. i.e. Using `with`
   1. Make sure to note the use of Python contexts here. An Ecosystem application can not be started without being run inside a Python context!
3. We start it on line 27.
4. Then finally, the `main` function is called.

The values we are passing to the base class `__init__` method are:
1. `app_config.name`, our application name as configured earlier
2. `app_config`, the application level configuration for our application.

That is it. All of it.

Once you are comfortable with this example, take a look at an Ecosystem [Echo-server](./example_echo_server.md).
