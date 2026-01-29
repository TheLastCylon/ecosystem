# Proper Fun

Before proceeding, if you have not done it yet, now is a great time to look at
configuring Ecosystem applications, [through environment variables](../configuration/through_environment_variables.md).

You did? Excellent!

Right, time to take off the training wheels, and get going with what Ecosystem
looks like in the real-world.

If you've been paying attention, I'm rather certain you've noticed that the
[Fun Factory example system](fun_factory/fun_factory.md). Is an
**entire messages based, distributed system**, comprising `7` servers and `1` client.
Created using less than 1000 lines of code ... For the **entire system**.

Well ... Strap in, because we are going to get that below 500, **and do it better**.

The code for this example can be found in the `examples/proper_fun` directory,
of this repository.

It does **exactly** what the [Fun Factory example](fun_factory/fun_factory.md) does. With a few critical
differences, that pushes it out of the example-arena, right into production-ready
code.

And believe it or not, but this is done through: **Removing code**!

First off, take a look at the
[examples/proper_fun/fortunes/fortunes.py](../../examples/proper_fun/fortunes/fortune.py)
code. You'll notice it has `4` fewer lines than the one in the [Fun Factory example](fun_factory/fun_factory.md).

Here's what has been removed:

```python
2: from ekosis.configuration.config_models import ConfigTCP
```

```python
10:     self._configuration.tcp = ConfigTCP(host="127.0.0.1", port=8100)
11:     self._configuration.stats_keeper.gather_period  = 60
12:     self._configuration.stats_keeper.history_length = 60
```

This is because we are going to set its host, port, gather-period and history
length, through environment variables.

And because we aren't setting the client in code, we don't need the import
line for `ConfigTCP`.

So yea, in this case, less is very definitely more.

You'll notice the same has been done for:
- [examples/proper_fun/joker/joker.py](../../examples/proper_fun/joker/joker.py)
- [examples/proper_fun/lottery/lottery.py](../../examples/proper_fun/lottery/lottery.py)
- [examples/proper_fun/magic_eight_ball/magic_eight_ball.py](../../examples/proper_fun/magic_eight_ball/magic_eight_ball.py)
- [examples/proper_fun/time_reporter/time_reporter.py](../../examples/proper_fun/time_reporter/time_reporter.py)
- [examples/proper_fun/tracker/tracker.py](../../examples/proper_fun/tracker/tracker.py)
- [examples/proper_fun/router/router.py](../../examples/proper_fun/router/router.py)

The next big difference, is the content of [examples/proper_fun/router/clients.py](../../examples/proper_fun/router/clients.py).

```python
from ekosis.clients import UDPClient

fortunes_client      = UDPClient("127.0.0.1", 8100)
joker_client         = UDPClient("127.0.0.1", 8200)
lottery_client       = UDPClient("127.0.0.1", 8300)
magic8ball_client    = UDPClient("127.0.0.1", 8400)
time_reporter_client = UDPClient("127.0.0.1", 8500)
tracker_client       = UDPClient("127.0.0.1", 8700)
```

Yup, we are going with UDP for this, so the system client in
[examples/proper_fun/router/client.py](../../examples/proper_fun/router/client.py)
has to change as well.

I'm certain you can see the import for `UDPClient` and where the UDP client
gets configured in that code.

Then, the last step: Setting the environment variables.

My apologies to the people using Windows, I honestly do not have a Windows machine.
Nor do I have the time/energy to set up a virtual machine to test a single script.
So again, my apologies, right now there isn't a `cmd` or `bat` script for this
example. I'll get to it, eventually. I am quite confident though, that if you got
this far in the examples, you are more than capable of figuring out what you'll need.

For the people with Linux/Unix/Other POSIX systems:

You'll notice a shell-script named
[`start_fun_factory.sh`](../../examples/proper_fun/start_fun_factory.sh)
in the `examples/proper_fun` directory.

Here's what's in there:

```shell
CURRENT_DIR="$(pwd)"
SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"
REPOSITORY_DIR="$(dirname "$EXAMPLES_DIR")"

echo "REPOSITORY_DIR: $REPOSITORY_DIR"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:/home/linuxbrew/.linuxbrew/bin:$PATH"

# Machine level configurations
export ECOENV_BUFFER_DIR=/tmp
export ECOENV_LOG_DIR=/tmp
export ECOENV_LOG_BUF_SIZE=1500
export ECOENV_STAT_GP=60
export ECOENV_STAT_HL=60

# Instance level configurations
export ECOENV_UDP_FORTUNE_0=127.0.0.1:8100
export ECOENV_UDP_JOKER_0=127.0.0.1:8200
export ECOENV_UDP_LOTTERY_0=127.0.0.1:8300
export ECOENV_UDP_MAGIC_EIGHT_BALL_0=127.0.0.1:8400
export ECOENV_UDP_TIME_REPORTER_0=127.0.0.1:8500
export ECOENV_UDP_ROUTER_0=127.0.0.1:8600
export ECOENV_UDP_TRACKER_0=127.0.0.1:8700

# Extra configs
export ECOENV_EXTRA_TRACKER_0_DB_FILE=/tmp/tracker-0-database.sqlite

cd "$REPOSITORY_DIR"

# Start the system
pipenv run python3 -m examples.proper_fun.fortunes.fortune                  -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.joker.joker                       -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.lottery.lottery                   -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.magic_eight_ball.magic_eight_ball -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.time_reporter.time_reporter       -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.router.router                     -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.tracker.tracker                   -i 0 -lfo &

cd "$CURRENT_DIR"
```

I use this to start the system in my environment. You might have to alter the
lines for `PYENV_ROOT` and `PATH`, but the rest should work as is.

Take note that:

1. I'm setting:
   - The machine level queue directory to: `/tmp`
   - The log file directory to: `/tmp`
   - The log file write buffer size to: `1500`
   - The stats/telemetry gathering period to: `60` seconds
   - The history length to: `60` i.e. One hour of history.
2. Then I configure the various UDP details for each of the components.
3. I use the `ECOENV_EXTRA_` feature, to set the location and name of the
   `[tracker]` component database. In 
   [examples/proper_fun/tracker/database.py](../../examples/proper_fun/tracker/database.py)
   I get it with `config.extra['DB_FILE']` and use its value as the path to the
   sqlite database file.
4. And finally, I start each of the servers as a background process, that only logs
   to file.

If you take the time to count the number of lines of code in this entire example.
You'll find that, once we remove white-space and comment lines, we are at a grand
total of: `476`!

Yup, an entire system, that includes telemetry, queueing, UDP communications and
actually works ... In less than `500` lines of code!

Even if you argue that the environment variable setting should also be counted,
we are still only at `489` lines.

Personally, I've never achieved so much, with so little code.

O and! If you want to get the [telemetry example](telemetry/telemetry.md)
working with this. All you have to do, is to alter the `-st tcp` option we set in
[examples/telemetry/telemetry_cron_script.sh](../../examples/telemetry/telemetry_cron_script.sh)
to be `-st udp`.

Go ahead, get it working, I think you'll be pleasantly surprised at the results
this little system can demonstrate.
