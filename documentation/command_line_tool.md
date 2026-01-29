# The Ecosystem command line tools

These tools allow you to interact with your Ecosystem applications, while they
are running. So doing things like:
- [Setting log level and log file buffer size](#setting-log-level-and-log-file-buffer-size-at-runtime)
- [getting statistical data](#getting-application-statistics), and
- Managing queues created with:
  - [`buffered_endpoint`](#managing-queues-created-through-buffered_endpoint-ie-queued-endpoint-manager-qem-for-short) or
  - [`buffered_sender`](#managing-queues-created-through-buffered_sender-ie-queued-sender-manager-qsm-for-short)

Go ahead try the statistics tool, run it with `-h` to see the help output.

```shell
python -m ekosis.cli.stat -h
```

What follows are examples of how to use these tools, and common use cases for them.

---
## Setting log level and log file buffer size, at runtime.
With Ecosystem applications, you can alter the log leve and log file buffer size,
on the fly. This can be quite useful for debugging in environments where the log
level, or the file buffer size is too high. Just remember to set both back to
what they are supposed to be.

Here's how:

Get help with: `python -m ekosis.cli.log -h`

### Log level
```shell
python -m ekosis.cli.log -st tcp -sd 127.0.0.1:8888 -l debug
```

### Log file buffer size
```shell
python -m ekosis.cli.log -st tcp -sd 127.0.0.1:8888 -b 20
```

---
## Getting application statistics
### for the current statistics gathering period
```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888
```
or
```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888 -type current
```
### for the last gathered period
```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888 -type gathered
```
### for the full list of historic periods
```shell
python -m ekosis.cli.stat -st tcp -sd 127.0.0.1:8888 -type full
```

---
## Managing queues created through `buffered_endpoint` i.e. Buffered Endpoint Manager. BEM for short
### Getting data about the queue
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times
```

### Pause and unpause receiving
#### pause
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -pr
```
#### unpause
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -ur
```

### Pause and unpause processing
#### pause
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -pp
```
#### unpause
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -up
```

### Pause and unpause both receiving and processing
#### pause
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -pa
```
#### unpause
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -ua
```

### Get the UUIDs for the first 10 entries in the `error` database
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -e10
```

### Move one specified entry in the `error` database to the `pending` database
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -rp1 -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Move all `error` database entries to the `pending` database
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -rpa
```

### Delete one specified entry from `error` database
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -pop -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Inspect one specified entry in the `error` database
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -ins -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Delete all entries in the `error` database
USE THIS WITH EXTREME CAUTION, MESSAGES CAN NOT BE RETRIEVED!!!
```shell
python -m ekosis.cli.qem -st tcp -sd 127.0.0.1:8888 -rk dice_roller.roll_times -clr
```

---
## Managing queues created through `buffered_sender`. i.e. Buffered Sender Manager, BSM for short.

### Getting data about the queue
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request
```

### Pause and unpause sending
#### pause
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -ps
```
#### unpause
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -us
```

### Get the UUIDs for the first 10 entries in the `error` database
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -e10
```

### Move one specified entry in the `error` database to the `pending` database
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -rp1 -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Move all `error` database entries to the `pending` database
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -rpa
```

### Delete one specified entry from `error` database
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -pop -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Inspect one specified entry in the `error` database
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -ins -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Delete all entries in the `error` database
USE THIS WITH EXTREME CAUTION, MESSAGES CAN NOT BE RETRIEVED!!!
```shell
python -m ekosis.cli.qsm -st tcp -sd 127.0.0.1:8888 -rk app.log_request -clr
```
