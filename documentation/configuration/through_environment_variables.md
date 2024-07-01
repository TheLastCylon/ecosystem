# Caution!
BEFORE YOU READ THIS. MAKE ABSOLUTELY CERTAIN YOU HAVE LEARNED ABOUT [APPLICATION NAMES AND RUNNING INSTANCES](./configuration.md).

You did?

Good!

Let's get into it then.

---
# Configuration using environment variables.

All Ecosystem environment variables start with: `ECOENV_`

All of them.

Even your environment variables that have nothing to do with Ecosystem, can start with `ECOENV_`

## Machine level configuration

What follows below, is a list of Ecosystem environment variables, that set things for all Ecosystem applications, running on the same machine.

### For directories/folders:
- `ECOENV_DEFAULT_DIR`
  - Set the default location for LOG and LOCK files ONLY.
  - Defaults:
    - On Windows: `C:`
    - On everything else: `/tmp`
- `ECOENV_LOCK_DIR`
  - Sets the location for LOCK files.
  - Default: The value of `ECOENV_DEFAULT_DIR`
- `ECOENV_LOG_DIR`
  - Sets the location for LOG files.
  - Default: The value of `ECOENV_DEFAULT_DIR`
- `ECOENV_QUEUE_DIR`
  - Sets the location for the sqlite queue database files to reside.
  - TAKE NOTE:
    - Ecosystem will NEVER try to use some kind of default for the location of queueing databases.
    - If your application uses things like `queued_endpoint`, you will have to explicitly set this location, for at least machine level.
    - Queue databases are simply too important to have their location left up to some kind of computed default.
    - Ecosystem forces you to be explicit about this, because losing these sqlite files, or having them in a location that you do not consciously know and keep track of, can cause disasters.

### For logging:
- `ECOENV_LOG_FORMAT`
  - Sets the format for log entries.
  - This is the format as specified and used by Python's logger.
  - More specifically, the use of `logging.Formatter`, as is available in Python's standard `import logging`
  - For more on what exactly you can do with that, please refer to the Python documentation.
  - The default used by Ecosystem is: `%(asctime)s.%(msecs)03d|%(levelname)s|%(filename)s|%(lineno)d|%(message)s`
- `ECOENV_LOG_DATE_FORMAT`
  - Sets the format for dates in log entries.
  - Here again, this is from Python's standard logging mechanisms.
  - For details about it, please refer to Python's documentation.
  - The default used by Ecosystem is: `%Y%m%d%H%M%S`
- `ECOENV_LOG_LEVEL`
  - Sets the logging level.
  - Valid options are: `debug`,`info`,`warn`,`error`,`critical`.
  - Default: `info`
- `ECOENV_LOG_COMPRESS`
  - When false or not set, log rotation done by Ecosystem applications, will not include compressing of rotated log files.
  - If set to have a value of `TRUE` the rotated log files will also be compressed.
    - This is NOT A GOOD THING for production environments.
    - Making your application deal with having to compress files, causes it to spend time doing that, every time a log file has to be rotated.
    - This is BAD for production environments!
    - Rather look at using tools like `logrotate` for this.
  - Default: `FALSE`
- `ECOENV_LOG_MAX_FILES`
  - The number of rotated log files to keep.
  - Default: 10
- `ECOENV_LOG_MAX_SIZE`
  - The size, in bytes, log files may reach before being rotated.
  - Default: 10737418240 from `(1024*1024*1024)*10 = 10,737,418,240` i.e. 10 mega-bytes

A word on log file names:

For an Ecosystem application, it's log file will always have the name `{application name}-{insance}.log`
Rotated log file names will be named `{application name}-{insance}.log.{rotation number}`

That means:
- For an application name: `my_cool_application`
- Running as instance: `0`
- The log file being written to will always be: `my_cool_application-0.log`
- Rotated log file names will look like:
  - `my_cool_application-0.log.1`, `my_cool_application-0.log.2`, `my_cool_application-0.log.3`, `my_cool_application-0.log.4`, `my_cool_application-0.log.5`
- The lower the appended number, the younger the rotated file is.
- Conversely: The higher it is, the older the logs are.


### For statistics:
- `ECOENV_STAT_GP`
  - The **Stat**istics **G**athering **P**eriod, in seconds.
  - Default: 300 i.e. 5 Minutes
- `ECOENV_STAT_HL`
  - The number of statistic period histories to keep. i.e. **Stat**istic **H**istory **L**ength.
  - Default: 12 i.e. 1 hour's worth of default gather period entries



## Application level configuration

You can adjust any of the above at application level, merely by creating an environment variable that also contains:
- your application name,
- in upper case,
- appended to the variable name you see above.

That means:
1. For an application name `my_cool_application`.
2. If you wanted instances of it, to have their log files in a location other than that set with `ECOENV_LOG_DIR`.
3. All you have to do, is create an environment variable named `ECOENV_LOG_DIR_MY_COOL_APPLICATION`, that is set to the location you wish to use.

## Instance level configuration

To take this down to instance level, you append the instance id, in uppercase, to the application level variable name.

That means:
1. For an application name `my_cool_application`.
2. If you want instances of `feeds_cats` and `feeds_dogs` to have their log files in different locations.
3. You would create environment variables named:
   1. `ECOENV_LOG_DIR_MY_COOL_APPLICATION_FEEDS_CATS` and
   2. `ECOENV_LOG_DIR_MY_COOL_APPLICATION_FEEDS_DOGS`

Now let us look at the configurations that can only be set at instance level.

## Instance level only configurations

### TCP, UDP and UDS configurations

#### TCP
- `ECOENV_TCP_{uppercase application name}_{uppercase instance}`
  - Configure the TCP server for an application instance.
  - The value you set is expected to be in the format `HOST:PORT`
  - i.e. `127.0.0.1:8888`
  - Default: none

#### UDP
- `ECOENV_UDP_{uppercase application name}_{uppercase instance}`
  - Configure the UDP server for an application instance.
  - Here again, the value you set is expected to be in the format `HOST:PORT`
  - i.e. `127.0.0.1:8889`
  - Default: none

#### UDS
- `ECOENV_UDS_{uppercase application name}_{uppercase instance}`
  - Configure the UDS server for an application instance.
  - This should be an absolute path to a file e.g. `/my/uds/socket/files/socket_file_name.sock`
  - Default: none
  - Take note:
    - If you make the basename portion of the path you set `DEFAULT` e.g. `/my/uds/socket/files/DEFAULT`
      - The socket file will:
        1. Be located in `/my/uds/socket/files` and
        2. have the name `{application name}_{instance}.uds.sock`
      - That means:
        1. For an application named: `my_cool_application`
        2. Being run as instance: `feeds_cats`
        3. Where `ECOENV_UDS_MY_COOL_APPLICATION_FEEDS_CATS` is set to: `/my/uds/socket/files/DEFAULT`
        4. The socket file will:
           1. Be located in `/my/uds/socket/files` and
           2. have the name `my_cool_application_feeds_cats.uds.sock`
    - If you do NOT use this, it is completely up to you to make sure:
      - the socket file names for every single running instance,
      - of every Ecosystem application,
      - running on any given single machine,
      - ARE UNIQUE to that running instance!

So yes, you can choose to administer it yourself. Personally though, I enjoy NOT having to worry about this kind of thing.

And now, let's take a look at something a little bit ... Extra.

### Extra!

I'm rather certain my fellow Software Developers out there, will appreciate this nifty little feature.

If you create an environment variable, having a name that:
- Starts with: `ECOENV_EXTRA_`
- followed by your application name in uppercase
- followed by your instance identifier in uppercase.
- followed by some arbitrary string.

The value of that environment variable will be made available for you, in the instance configuration within your application.

That means:
1. For an application named: `my_cool_application`
2. Being run as instance: `feeds_cats`
3. Where an environment variable named `ECOENV_EXTRA_MY_COOL_APPLICATION_FEEDS_CATS_DATABASE_NAME` has been created.
4. There will, in the instance configuration available in your application at runtime, be an entry named `DATABASE_NAME`, that has been set to the value of `ECOENV_EXTRA_MY_COOL_APPLICATION_FEEDS_CATS_DATABASE_NAME`
5. You'll be able to access it using something like: `self._configuration.extra['DATABASE_NAME']`

Again: Yes. I know. You're welcome. It's my pleasure, I assure you!

Now let's take a look at what you'll need for [configuration using files](./through_configuration_files.md).
