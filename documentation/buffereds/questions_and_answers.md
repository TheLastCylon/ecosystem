# Ecosystem Buffered Endpoints and Senders, Q&A.

---
## Where are the queue databases located?

As discussed in
[configuration through environment variables](../configuration/through_environment_variables.md),
the location of where your buffer databases are kept, is set using the `ECOENV_BUFFER_DIR` environment variable.

There is no default for this! You have to set it explicitly.

I'm going to repeat the reasons for this here, just in case you weren't paying
attention when reading the configuration documentation:

- Ecosystem will NEVER try to use some kind of default for the location of
  buffering databases.
- If your application uses things like `buffered_endpoint` or `buffered_sender`, you
  will have to explicitly set this location, for at least machine level. Or your
  application will not start.
- Buffer databases are far too important to have their location left up to some
  kind of computed default.
- Ecosystem forces you to be explicit about this, because losing these
  [Sqlite](https://sqlite.org) database files, or having them in a location that
  you do not **consciously know and keep track of**, can cause disasters.

Also, again:
You can configure this location at machine, application and instance level.

---
## What are they named?

- When using `buffered_endpoint` they are:
  1. `{application name}-{instance}-{route key}-endpoint-pending.sqlite` and,
  2. `{application name}-{instance}-{route key}-endpoint-error.sqlite`
- for the `pending` and `error` databases respectively.


- For `buffered_sender`:
  1. `{application name}-{instance}-{route key}-sender-pending.sqlite`
  2. `{application name}-{instance}-{route key}-sender-error.sqlite` 
- for the `pending` and `error` databases respectively.

That means:

- For an application named: `my_application`
- Being run as instance: `0`


- Having a `buffered_endpoint`, where the route key is `app.call_me`
- The `pending` database file name will be:
  - `my_application-0-app.call_me-endpoint-pending.sqlite` 
- The `error` database file name will be:
  - `my_application-0-app.call_me-endpoint-error.sqlite` 


- If it has a `buffered_sender`, where the route key is `app.send_this`
- The `pending` database file name will be:
  - `my_application-0-app.send_this-sender-pending.sqlite` 
- The `error` database file name will be:
  - `my_application-0-app.send_this-sender-error.sqlite` 

---
## Can I access them using `sqlite` from the command line.

Yes.

Should you though?

NO!

If you are resorting to this, something has gone very, very, very wrong!

There are also better ways of doing things, through Ecosystem.

Take a look at [standard endpoints for queue management](./standard_endpoints_for_management.md)
