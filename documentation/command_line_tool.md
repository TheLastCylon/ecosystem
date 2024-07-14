# The Ecosystem command line tool

This tool allows you to interact with your Ecosystem applications, while they
are running. So doing things like:
- [getting statistical data](#getting-application-statistics), and
- Managing queues created with:
  - [`queued_endpoint`](#managing-queues-created-through-queued_endpoint) or
  - [`queued_sender`](#managing-queues-created-through-queued_sender)

Go ahead and run it with `-h` to see the help output.

```shell
python -m ecosystem.command_line_tool.cli -h
```

What follows are examples of how to use it for common use cases.

---
## Getting application statistics
### for the current statistics gathering period
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac stat
```
or
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac stat \
  -stat current
```
### for the last gathered period
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac stat \
  -stat gathered
```
### for the full list of historic periods
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac stat \
  -stat full
```

---
## Managing queues created through `queued_endpoint`
### Getting data about the queue
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times
```

### Pause and unpause receiving
#### pause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -pr
```
#### unpause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -ur
```

### Pause and unpause processing
#### pause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -pp
```
#### unpause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -up
```

### Pause and unpause both receiving and processing
#### pause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -pa
```
#### unpause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -ua
```

### Get the UUIDs for the first 10 entries in the `error` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -e10
```

### Move one specified entry in the `error` database to the `pending` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -rp1 \
  -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Move all `error` database entries to the `pending` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -rpa
```

### Delete one specified entry from `error` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -pop \
  -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Inspect one specified entry in the `error` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -ins \
  -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Delete all entries in the `error` database
USE THIS WITH EXTREME CAUTION, MESSAGES CAN NOT BE RETRIEVED!!!
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8888 \
  -ac qem \
  -rk dice_roller.roll_times \
  -clr
```

---
## Managing queues created through `queued_sender`

### Getting data about the queue
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request
```

### Pause and unpause sending
#### pause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -pa
```
#### unpause
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -ua
```

### Get the UUIDs for the first 10 entries in the `error` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -e10
```

### Move one specified entry in the `error` database to the `pending` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -rp1 \
  -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Move all `error` database entries to the `pending` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -rpa
```

### Delete one specified entry from `error` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -pop \
  -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Inspect one specified entry in the `error` database
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -ins \
  -rid [THE UUID OF THE ENTRY YOU WANT TO MOVE]
```

### Delete all entries in the `error` database
USE THIS WITH EXTREME CAUTION, MESSAGES CAN NOT BE RETRIEVED!!!
```shell
python -m ecosystem.command_line_tool.cli \
  -st tcp \
  -sd 127.0.0.1:8600 \
  -ac qsm \
  -rk app.log_request \
  -clr
```
