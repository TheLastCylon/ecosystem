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

It should look something like this:

```
usage: cli.py [-h] -st {tcp,udp,uds} -sd <server details> [-ac {stat,qem}] [-stat {current,gathered,full} | -rk <route_key>] [-dt | -pr | -pp | -pa | -ur | -up | -ua | -e10 | -rp1 | -rpa | -ins | -pop | -clr] [-rid <request uuid>]

options:
  -h, --help            show this help message and exit
  -st {tcp,udp,uds}, --server_type {tcp,udp,uds}
                        The type of server you want to interact with.
  -sd <server details>, --server_details <server details>
                        Connection details for the server. If TCP or UDP, format should be HOST:PORT. If UDS, the path to the socket file.
  -ac {stat,qem}, --action {stat,qem}
                        The action you want to perform. 'stat' = get statistics or 'qem' = queued endpoint management. Default is 'stat'.
  -stat {current,gathered,full}, --statistics_type {current,gathered,full}
                        The statistics type you want to retrieve. Default is 'current'.
  -rk <route_key>, --route_key <route_key>
                        The route key of the queue you wish to interact with.
  -dt, --data           Get data about a queue.
  -pr, --pause_receiving
                        Pause receiving on a queue.
  -pp, --pause_processing
                        Pause processing on a queue.
  -pa, --pause_all      Pause both receiving and processing on a queue.
  -ur, --unpause_receiving
                        UN-Pause receiving on a queue.
  -up, --unpause_processing
                        UN-Pause processing on a queue.
  -ua, --unpause_all    UN-Pause both receiving and processing on a queue.
  -e10, --error_10      Get the first 10 uuids in an error queue.
  -rp1, --reprocess_one
                        Reprocess a specified entry in an error queue. [Requires -rid].
  -rpa, --reprocess_all
                        Reprocess all entries in an error queue.
  -ins, --inspect_request
                        View a request on an error queue. [Requires -rid].
  -pop, --pop_request   Pop a request from an error queue. [Requires -rid].
  -clr, --clear         Clear an error queue completely. WARNING: All requests in the error queue are deleted!
  -rid <request uuid>, --request_uid <request uuid>
                        The UUID for an item in a queue.
```

To be continued ...
