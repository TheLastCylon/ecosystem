# The fun factory

This example, gives you a better idea of what Ecosystem can do for you.

I would like you to keep in mind:

With this example, what I'm **NOT** doing, and **NOT** having to do, is **far
more important** than what is being done.

For instance:
- This **entire** system is done with less than 1000 lines of code. Once you get rid of all the white-space and comment lines, it doesn't even reach 600 lines of code.
- Nowhere in this example, will you see mention of having to install things like Kafka or ZeroMQ.
- Nothing even resembling docker or cloud services, are required.

Yes, Ecosystem is all about having an ECOnomic-System!

And yes, people have made serious money with systems as simple as this example.
In fact, this example is inspired by a business I used to work for, not too long ago.

If you are from the generation that thought sending text messages using a phone
was neat, you likely interacted with a business like that, at least once.

Enough rambling though, lets get on with it.

## The system.
What you see below, is a diagram of the various components of the system, showing
the communication links between them.

```
                        +-->[fortunes]
                        |
                        +-->[joker]
                        |
[client]<--->[router]<--+-->[lottery]
                |       |
                |       +-->[magic_eight_ball]
                V       |
             [tracker]  +-->[time_reporter]
```

Below is a table of the components and the commands you can use to start them.

| component            | command                                                                 |
|----------------------|-------------------------------------------------------------------------|
| `[fortunes]`         | `python -m examples.fun_factory.fortunes.fortune -i 0`                  |
| `[joker]`            | `python -m examples.fun_factory.joker.joker -i 0`                       |
| `[lottery]`          | `python -m examples.fun_factory.lottery.lottery -i 0`                   |
| `[magic_eight_ball]` | `python -m examples.fun_factory.magic_eight_ball.magic_eight_ball -i 0` |
| `[time_reporter]`    | `python -m examples.fun_factory.time_reporter.time_reporter -i 0`       |
| `[tracker]`          | `python -m examples.fun_factory.tracker.tracker -i 0`                   |
| `[router]`           | `python -m examples.fun_factory.router.router -i 0`                     |
| `[client]`           | `python -m examples.fun_factory.router.client`                          |

With the exception of `[client]`, the order in which you start these applications does not matter.

When you start all this up, make sure to start `[client]` last.

## The components

None of:
- `[fortunes]`
- `[joker]`
- `[lottery]`
- `[magic_eight_ball]`
- `[time_reporter]` or
- `[client]`

Do anything you have not encountered in previous examples. 

As for `[tracker]`, other than having a database, it does nothing you've not seen yet.

The real demonstrations for this example, are in `[router]`.

So, let's do a brief overview of each of the components, then we'll look at `[router]` in detail.

---
#### `[client]`
Is a message generator.

The code for it can be found in [examples/fun_factory/router/client.py](../../../examples/fun_factory/router/client.py)


- It randomly selects a message from a list, then sends it to `[router]`.
- The list of messages are: `fortune`, `joke`, `lotto`, `time` and `question`.
- You can run the client with: `python -m examples.fun_factory.router.client SLEEP_PERIOD`
  - Where `SLEEP_PERIOD` is how long, in seconds or fractions of a second, you want to have the client sleep between generating messages.
  - If you don't specify `SLEEP_PERIOD` it defaults to `0.1` seconds. i.e. a tenth of a second.
  - Remember to start the client only after everything else is started.


- **IMPORTANT WARNING**:
  - There is a lot of random number generation, UUID generation, and random list selections, happening with this system.
  - This can be very CPU intensive!!!
  - If you set `SLEEP_PERIOD` to `0`, you will easily push your CPU usage to `80%`. And it will stay at that level until `[router]` has sent all queued notifications to `[tracker]`.
  - Yes, stopping the client only stops message generation. You can fill the `[router]` sending-queues with tens of thousands of messages, in under a minute.
  - I have successfully tested this system with `SLEEP_PERIOD` set to `0`, just be aware that your CPU-fan will go nuts.
  - That means: Do **not** run it like this for too long. It is very unlikely, but your CPU could get fried.
  - This kind of system typically runs on purpose built servers, made by companies like Dell, and are kept in air-conditioned server farms. Exactly because CPUs can and do get hot.
  - Also:
    - Nothing prevents you from running multiple instance of `[client]`, from multiple terminals. The system will deal with it.
    - Just remember: It's your CPU, not mine.

---
#### `[fortunes]`
Responds with a fortune-cookie fortune, or quote, obtained from a text file.


- The data for the text file, was copied from [Brian Clapper's fortune cookie database](https://github.com/bmc/fortunes).
- Run using: `python -m examples.fun_factory.fortunes.fortune -i 0`
- The Code is located in: `examples/fun_factory/fortunes`

---
#### `[joker]`
Responds with a dad joke, contained in a text file.


- The source of this is my own collection of over 200 dad jokes, that I enjoy annoying humans with.
- Run using: `python -m examples.fun_factory.joker.joker -i 0`
- The Code is located in: `examples/fun_factory/joker`

---
#### `[lottery]`
Is a component that generates lottery numbers.


- Specifically for a: 6 choice with bonus ball lottery, that has 52 balls to choose from.
- Run using: `python -m examples.fun_factory.lottery.lottery -i 0`
- The Code is located in: `examples/fun_factory/lottery`

---
#### `[magic_eight_ball]`
Responds to a question, with a typical magic 8-ball answer.


- Run using: `python -m examples.fun_factory.magic_eight_ball.magic_eight_ball -i 0`
- The Code is located in: `examples/fun_factory/magic_eight_ball`

---
#### `[time_reporter]`
Responds with the current time, in a nice format.


- Run using: `python -m examples.fun_factory.time_reporter.time_reporter -i 0`
- The Code is located in: `examples/fun_factory/time_reporter`

---
#### `[tracker]`
Is basically a message logger, that keeps requests received and responded too, by `[router]`, in a database


- Run using: `python -m examples.fun_factory.tracker.tracker -i 0`
- The Code is located in: `examples/fun_factory/tracker`

---
#### `[router]`
Is the message router,


- It takes what the client sends in, maps it to the appropriate service, gets the response, then passes it back too `[client]`.
- While it is doing this:
  - It also sends message to `[tracker]`, for every message received from `[client]`.
  - Both the message received from `client` as well as the response returned to `[client]` are logged this way.
  - Because `[router]` has to respond to `[client]` as fast as possible, the work it does to notify `[tracker]` of the messages, may not interfere with its responses to `[client]`
  - Run using: `python -m examples.fun_factory.router.router -i 0`
  - The Code is located in: `examples/fun_factory/router`

Now let's move on and take a look at the [code for `[router]`](./router_code.md)
