# Queued endpoints, Q&A.

---
## Where are the queue databases located?

As discussed in
[configuration through environment variables](../configuration/through_environment_variables.md),
the location of where your queue databases is, set using the `ECOENV_QUEUE_DIR` environment variable.

There is no default for this! You have to set it explicitly.

I'm going to repeat the reasons for this here, just in case you weren't paying
attention when reading the configuration documentation:

- Ecosystem will NEVER try to use some kind of default for the location of queueing databases.
- If your application uses things like `queued_endpoint`, you will have to explicitly set this location, for at least machine level.
- Queue databases are simply too important to have their location left up to some kind of computed default.
- Ecosystem forces you to be explicit about this, because losing these sqlite files, or having them in a location that you do not consciously know and keep track of, can cause disasters.

Also, again:
You can configure this location at machine, application and instance level.

---
## What are they named?

- For the incoming queue:
  - `{application name}-{instance}-{route key}-queue-incoming.sqlite`
- For the error queue:
  - `{application name}-{instance}-{route key}-queue-error.sqlite`

That means:

- For an application named: `dice_roller_example`
- Being run as instance: `0`
- Having a `queued_endpoint`, where the route key is `dice_roller.roll_times`
- The incoming queue file name will be:
  - `dice_roller_example-0-dice_roller.roll_times-queue-incoming.sqlite` 
- The error queue file name will be:
  - `dice_roller_example-0-dice_roller.roll_times-queue-error.sqlite`

---
## Can I access them using `sqlite` from the command line.

Yes.

Should you though?

NO!

If you are resorting to this, something has gone very, very, very wrong!

There are also better ways of doing things, through Ecosystem.

Take a look at [standard endpoints for queue management](./standard_endpoints_for_management.md)
