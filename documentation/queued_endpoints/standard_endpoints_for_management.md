# Queued endpoints: Standard endpoints, for management:

Ecosystem provides a host of standard endpoints ripe and ready for you to use,
when you need to get down and dirty with queues.

They are:
- `eco.queued_handler.data`
- `eco.queued_handler.receiving.pause`
- `eco.queued_handler.receiving.unpause`
- `eco.queued_handler.processing.pause`
- `eco.queued_handler.processing.unpause`
- `eco.queued_handler.all.pause`
- `eco.queued_handler.all.unpause`
- `eco.queued_handler.errors.get_first_10`
- `eco.queued_handler.errors.reprocess.all`
- `eco.queued_handler.errors.clear`
- `eco.queued_handler.errors.reprocess.one`
- `eco.queued_handler.errors.pop_request`
- `eco.queued_handler.errors.inspect_request`

More detail will follow as I get to update this document.

For now, you can use the Ecosystem command line tool to play.

Try this:

```shell
python -m ecosystem.command_line_tool.cli -st tcp -sd 127.0.0.1:8888 -a qem -rk dice_roller.roll_times -dt
```

Until I get to flesh out this document, you can rely on the help output of this tool with:

```shell
python -m ecosystem.command_line_tool.cli -h
```

To be continued ...
