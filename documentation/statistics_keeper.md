# Statistics (Real-time Telemetry) made easy. 

## Why it exists.

In every single business, one needs to know things like:
- How many times users have interacted with a particular endpoint.
- How long an application has been up.
- How big are queues at any given time.
- And way, way more.

I've seen businesses go to ridiculous lengths to get these kinds of answers from
their systems. To the extent where they resort to log aggregation, or even
transmitting their raw logs to a 3rd party service.

Given how easy it is to just get your applications to report their own telemetry,
I've never seen the point behind either log aggregation or spending money on a
3rd party service for this. Besides, neither of those solutions give you
real-time telemetry.

Once you have an endpoint in an application, that allows you to get its telemetry
on the fly. You can put a real-time analytics solution like
[InfluxDB](https://www.influxdata.com/) in place, and simply feed it the
application's telemetry, through something as simple as a cron job.
And there you go ... Job done!

If you find that hard to believe, here's an image of a dashboard I put
together for the [Fun Factory example](./examples/fun_factory/fun_factory.md).

![Fun Factory Dashboard](./images/fun_factory_statistics_2.png)

What you are looking at there, is real-time telemetry, retrieved from an entire
system. It includes the number of times every endpoint in each of the services
was called, as well as the queue sizes for both the `[router]` and `[tracker]`
services.

So. Why not just have telemetry tracking, reporting and an endpoint, in your
applications?

Why waste money on 3rd party services, or live without real-time telemetry, when
all of that could be part of your system already?

## The Ecosystem statistics keeper.

Yes! Ecosystem provides a lot of statistics gathering, out of the box.

Just having an `endpoint` in your application causes Ecosystem to start tracking
data about that endpoint. The same thing happens for `queued_endpoint` and
`queued_sender`.

And no, you don't have to write a single line of code for it! Just the act
of decorating a function with `endpoint`, `queued_endpoint` or `queued_sender`,
does this for you already.

Even the endpoint that allows you to retrieve the telemetry data, already exists!

That end point is: `eco.statistics.get`

---
### The current statistical period
Go ahead, start up the [dice roller example](./examples/dice_roller/dice_roller.md)
and run its [client](./examples/dice_roller/client.md) a dozen or so times.

Then you can use either `netcat`, or the Ecosystem command line tool from your
terminal:

For `netcat` use this command:
```shell
echo '{"route_key": "eco.statistics.get", "data": {"type": "current"}, "uid": "abcdef01-abcd-abcd-abcd-abcdef012345"}' | nc localhost 8888
```

If you don't have `netcat` on your machine, try the Ecosystem command line tool with:

```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888 -type current
```

The output from the Ecosystem command line tool won't be the exact same as the
responses discussed below. All the data will be there though, and it will be
beautified for you.

**Note:** I'm showing protocol level responses in this document, because one will typically
want to use that when writing data to a real-time analytics database, rather than
the responses from a command line tool.

With the raw responses, you'll get something like what we have below, if you put
it through a JSON beautifier of some kind first:

```json
{
   "data" : {
      "statistics" : {
         "application" : {
            "instance" : "0",
            "name" : "dice_roller_example"
         },
         "endpoint_data" : {
            "dice_roller" : {
               "guess"      : { "call_count" : 23, "p95" : 5.03455034049693e-05, "p99" : 5.66645455546677e-05 },
               "roll"       : { "call_count" : 23, "p95" : 3.58768025762401e-05, "p99" : 4.79854423610959e-05 },
               "roll_times" : { "call_count" : 23, "p95" : 5.27693984622601e-05, "p99" : 5.75694638246205e-05 }
            },
            "eco" : {
               "error_states" : {
                  "clear" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "get"   : { "call_count" : 0, "p95" : -1, "p99" : -1 }
               },
               "queued_handler" : {
                  "all" : {
                     "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  },
                  "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "errors" : {
                     "clear"           : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "get_first_10"    : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "pop_request"     : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "reprocess"       : {
                        "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "processing" : {
                     "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  },
                  "receiving" : {
                     "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  }
               },
               "queued_sender" : {
                  "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "errors" : {
                     "clear"           : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "get_first_10"    : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "pop_request"     : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "reprocess"       : {
                        "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "send_process" : {
                     "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  }
               },
               "statistics" : {
                  "get" : { "call_count" : 2, "p95" : 0.00138424100441625, "p99" : 0.00138424100441625 }
               }
            }
         },
         "queued_endpoint_sizes" : {
            "dice_roller" : {
               "roll_times" : { "error" : 17, "pending" : 0 }
            }
         },
         "timestamp" : 1722188241.29274,
         "uptime" : 3809.29274368286
      }
   },
   "status" : 0,
   "uid" : "abcdef01-abcd-abcd-abcd-abcdef012345"
}
```

If you look at the `call_count` values in this JSON structure, you'll notice I
did `23` calls to each of the `dice_roller.guess`, `dice_roller.roll`, and
`dice_roller.roll_times` endpoints.

Even the 2 calls I made to `eco.statistics.get` are there.

You'll also notice values for `p95` and `p99`. These are kind of special, they
indicate that
- In the case of `p95`: The longest duration, for 95% of the calls to this
  endpoint. In seconds.
  - Pay attention to the values you see there, they are shown in scientific
    notation.
  - So `5.03455034049693e-05` is actually: `0.0000503455034049693` seconds.
  - That is about `50` microseconds.
- In the case of `p99`: This indicates the longest duration, for 99% of the
  calls to this endpoint.
- This can be very useful in finding which endpoints in your application,
  need some attention in terms of optimisation for speed.
- If an endpoint has not been called during the period statistics are being
  requested for, these will have a value of `-1`, in order to clearly
  indicate that there is no data to work with.

The sizes of the `incomming` and `error` queue databases for the
`dice_roller.roll_times` queued endpoint, are also there.

`timestamp` is the time at which I made the call to `eco.statistics.get`, and
`uptime` is how many seconds the
[dice roller example](./examples/dice_roller/dice_roller.md) has been running
since I started it up.

Pretty cool, right?

Well, hold on to your hat anyway: This gets better!

---
### The last gathered statistical period

The response you saw above, is just for the current 5-minute period of statistical
gathering.

Allow the [dice roller example](./examples/dice_roller/dice_roller.md) to run
more than 5 minutes, and you'll be able to use this `netcat` command from your terminal:

```shell
echo '{"route_key": "eco.statistics.get", "data": {"type": "gathered"}, "uid": "abcdef01-abcd-abcd-abcd-abcdef012345"}' | nc localhost 8888
```

If you'd rather play with the Ecosystem command line tool, use this:

```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888 -type gathered
```

The response you get, is all the gathered statistics, for the last gathering
period.

The default gathering period for an Ecosystem application, is `300` seconds. i.e.
`5` minutes. You can adjust this by setting the `ECOENV_STAT_GP` environment
variable on your system. For more on that, see the documentation on
[configuration through environment variables](./configuration/through_environment_variables.md).

Moving on though.

Yes, you can use the first `netcat` command I showed you, where `type` is set
to `current`, to get the situation as it is, at the time you execute the command
on your terminal.

The one where `type` is set to `gathered`, gives you the data as it was, for
the 5-minute period before the current gathering period.

Here's what I got:

```json
{
   "data" : {
      "statistics" : {
         "application" : {
            "instance" : "0",
            "name" : "dice_roller_example"
         },
         "endpoint_data" : {
            "dice_roller" : {
               "guess" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
               "roll" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
               "roll_times" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
            },
            "eco" : {
               "error_states" : {
                  "clear" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "get" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
               },
               "queued_handler" : {
                  "all" : {
                     "pause" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  },
                  "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "errors" : {
                     "clear" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "get_first_10" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "pop_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "reprocess" : {
                        "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "processing" : {
                     "pause" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  },
                  "receiving" : {
                     "pause" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  }
               },
               "queued_sender" : {
                  "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "errors" : {
                     "clear" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "get_first_10" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "pop_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "reprocess" : {
                        "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "send_process" : {
                     "pause" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  }
               },
               "statistics" : {
                  "get" : { "call_count" : 1, "p95" : 0.000837851002870593, "p99" : 0.000837851002870593 }
               }
            }
         },
         "queued_endpoint_sizes" : {
            "dice_roller" : {
               "roll_times" : {
                  "error" : 0,
                  "pending" : 0
               }
            }
         },
         "timestamp" : 1722187136.76713,
         "uptime" : 2704.76713085175
      }
   },
   "status" : 0,
   "uid" : "abcdef01-abcd-abcd-abcd-abcdef012345"
}
```

You'll notice for that period:
- the only call I made was too `eco.statistics.get`.

In this case, `timestamp` is the unix-timestamp at which this set of statistics
were gathered, and `uptime` is how long the application has been running, at the
time the statistics gathering took place.

If you are impressed by this, you might want to get some tape to hold your hat down.
It gets even better!

---
### The full statistical history.

By default, Ecosystem will keep `12` gathered periods as a history.
i.e. 1-hours worth of gathered statistics.

You can adjust this of course, using the `ECOENV_STAT_HL` environment variable.
Again, see the documentation on
[configuration through environment variables](./configuration/through_environment_variables.md), for more on that.

If you allow the [dice roller example](./examples/dice_roller/dice_roller.md) to
run for about 15 minutes, you'll be able to use this `netcat` command, from your terminal:

```shell
echo '{"route_key": "eco.statistics.get", "data": {"type": "full"}, "uid": "abcdef01-abcd-abcd-abcd-abcdef012345"}' | nc localhost 8888
```

Again, here's the Ecosystem command line tool, equivalent:

```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888 -type full
```

Here's what I got:

```json
{
   "data" : {
      "statistics" : [
         {
            "application" : {
               "instance" : "0",
               "name" : "dice_roller_example"
            },
            "endpoint_data" : {
               "dice_roller" : {
                  "guess"      : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "roll"       : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "roll_times" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
               },
               "eco" : {
                  "error_states" : {
                     "clear" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "get"   : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  },
                  "queued_handler" : {
                     "all" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     },
                     "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "errors" : {
                        "clear"           : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "get_first_10"    : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "pop_request"     : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "reprocess"       : {
                           "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                           "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                        }
                     },
                     "processing" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     },
                     "receiving" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "queued_sender" : {
                     "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "errors" : {
                        "clear"           : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "get_first_10"    : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "pop_request"     : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "reprocess"       : {
                           "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                           "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                        }
                     },
                     "send_process" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "statistics" : {
                     "get" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  }
               }
            },
            "queued_endpoint_sizes" : {
               "dice_roller" : {
                  "roll_times" : { "error" : 17, "pending" : 0 }
               }
            },
            "timestamp" : 1722189539.8746,
            "uptime" : 5107.87459921837
         },
         .
         .
         .
         .
         .
         .
         .
         {
            "application" : {
               "instance" : "0",
               "name" : "dice_roller_example"
            },
            "endpoint_data" : {
               "dice_roller" : {
                  "guess"      : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "roll"       : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                  "roll_times" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
               },
               "eco" : {
                  "error_states" : {
                     "clear" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "get"   : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  },
                  "queued_handler" : {
                     "all" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     },
                     "data" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "errors" : {
                        "clear"           : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "get_first_10"    : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "pop_request"     : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "reprocess"       : {
                           "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                           "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                        }
                     },
                     "processing" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     },
                     "receiving" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "queued_sender" : {
                     "data"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                     "errors" : {
                        "clear"           : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "get_first_10"    : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "inspect_request" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "pop_request"     : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "reprocess"       : {
                           "all" : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                           "one" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                        }
                     },
                     "send_process" : {
                        "pause"   : { "call_count" : 0, "p95" : -1, "p99" : -1 },
                        "unpause" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                     }
                  },
                  "statistics" : {
                     "get" : { "call_count" : 0, "p95" : -1, "p99" : -1 }
                  }
               }
            },
            "queued_endpoint_sizes" : {
               "dice_roller" : {
                  "roll_times" : { "error" : 0, "pending" : 0 }
               }
            },
            "timestamp" : 1722186235.48122,
            "uptime" : 1803.48122477531
         }
      ]
   },
   "status" : 0,
   "uid" : "abcdef01-abcd-abcd-abcd-abcdef012345"
}
```

You'll notice this is a list of entries, each one with their details and
timestamps of when they were gathered and all the other data you've seen in the
previous sections.

Again:

All of this exists, you don't have to write a single line of code! It's already
there!

If your hat has been bothering you, you might want to take it off at this point
because: It! Gets! Even! Better!

---
### Adding custom statistics

The `StatisticsKeeper` class, is implemented as a singleton, that you can import
into any of your Python modules:

```python
from ekosis.state_keepers.statistics_keeper import StatisticsKeeper
```

From there you can get an instance of it with:

```python
stats_keeper = StatisticsKeeper()
```

And now you can add your own statistics to your Ecosystem application.

```python
stats_keeper.set_statistic_value("log.this.statistic", 0)
```

Note that the `.` character is special. It allows you to keep groups of statistics.

With this example, when you use one of the `netcat` commands you've seen above.

You'll see it listed as:

```json
"log" : {
  "this" : {
    "statistic": 0
  }
}
```

You can also increment and decrement with:

```python
stats_keeper.increment("log.this.statistic")
stats_keeper.decrement("log.this.statistic")
```

You can even do so with a value:

```python
stats_keeper.increment("log.this.statistic", 5)
stats_keeper.decrement("log.this.statistic", 5)
```

All of this, without resorting to log aggregation, or transmitting logs to 3rd
parties for analysis.

Ecosystem ... Job! Done!
