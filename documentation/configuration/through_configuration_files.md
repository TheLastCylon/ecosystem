# Caution!
BEFORE YOU READ THIS. MAKE ABSOLUTELY CERTAIN YOU HAVE LEARNED ABOUT [APPLICATION NAMES AND RUNNING INSTANCES](./configuration.md).

You did?

Good!

Here we go.

---

# Configuration with files.

## Ecosystem will never support default configuration, through files!

Ecosystem has never, does not currently, and will never allow for default
configuration, through files. It does not do any kind of searching for configuration
files or default setup using configuration files.

It! Never! Will!

The simple fact is: Configuration files can end up in code repositories, that are
vulnerable to attack and exposure.

It's NEVER a good idea to have such files in a repository, but mistakes can and
do happen. Even the best among us, has an off day now and then.

What's worse though, is if those configuration files end up being used in a production
environment, because the framework tries to be clever about how it sets things up.
Causing the accidental inclusion of configuration files in a repository, to end
up being used for a production environment.

So. No!

Ecosystem does not, and will not do any kind of default configuration file searching.

Not now. NOT EVER!

Anyone who even approaches this subject, will instantly be suspected of attempting a
social engineering attack, and subsequently blocked on every conceivable communication
channel to me.

Don't even ask for it. The decision is FINAL!

If you feel this is harsh, its only because you haven't been around long enough,
to have seen entire systems go down, because of this kind of thing.

So, again: Do! Not! Even! Ask! For! This!

If you use configuration files in your Ecosystem production environments. It will
be because YOU made the choice to do so. And have explicitly told every single
instance, of every single Ecosystem application, to use a configuration file.

## This is for development environments!

That being said, during the software development process, it's an absolute pain for
Software Developers to make sure all the required environment variables needed,
are set. And get set, every single time the machine they work on, has to be restarted.
This becomes even more painful, when you have to have several applications running,
in order to test the one you are working on.

Ecosystem's configuration through files, is intended as a means to ease the lives
of the people who develop software with it. And to speed up the development process.

## Configuration files overwrite settings done with environment variables.

Ecosystem will always try to load as much configuration as it can, from environment
variables. When there are none, it will do it's best to select appropriate defaults
for things like:
- the location of log and lock files,
- the gathering period for statistics and how much statistical history to keep.

The act of telling an Ecosystem application, to load its configuration from a file, causes
the configuration it built from environment variables, to be overwritten with what ever
is in the configuration file.

Because one has to be explicit about loading a configuration file, they are considered
senior to environment variables, in terms of what they set.

It's quite impossible to UN-set something in a configuration file though. So, if
there is an environment variable that causes the application to have a TCP server.
All you can do with a configuration file, is to alter the host and port of that TCP server.
You can't set the application to NOT have a TCP server, if there is an environment variable
that causes it. This is true for all other settings. So, if you want only stuff in your
configuration file to be used, don't set environment variables for anything you don't want used.

## Specifying the configuration file you want to use.

In order to get an Ecosystem application to load its configuration from a file,
you have to explicitly invoke it with a path to the file you want to use.

This is done using the `-c` or `--config_file` command line option.

So, when you do something like: `python ./my_cool_application.py -i 0 -c ./my_config.json`

If `my_cool_application.py` is an Ecosystem application, you are telling it to run as instance `0`,
and load its configuration from a file named `my_config.json`, located in the current directory.

## The content of configuration files.

Finally, we get to the content of configuration files. Let's take a look at a simple example:

```json
{
    "instances" : {
        "0": {
            "tcp" : {
               "host" : "127.0.0.1",
               "port" : 1234
            }
        }
    }
}
```

This configuration file, tells Ecosystem that when the application using this
file is set to run as instance `0`, that instance should have its TCP server
listening on host `127.0.0.1` and port `1234`

Let's take a look at a complete configuration, for a single instance:

```json
{
    "instances": {
        "feeds_cats": {
            "lock_directory"  : "/tmp/lock_files",
            "buffer_directory" : "/tmp/buffer_files",
            "stats_keeper"    : {
               "gather_period"  : 300,
               "history_length" : 12
            },
            "tcp" : {
               "host" : "127.0.0.1",
               "port" : 8000
            },
            "udp" : {
               "host" : "127.0.0.1",
               "port" : 8001
            },
            "uds" : {
               "directory"        : "/tmp/socket_files",
               "socket_file_name" : "DEFAULT"
            },
            "logging"         : {
                "format"       : "%(asctime)s.%(msecs)03d|%(levelname)s|%(filename)s|%(lineno)d|%(message)s",
                "date_format"  : "%Y%m%d%H%M%S",
                "level"        : "debug",
                "file_logging" : {
                    "directory"         : "/tmp/log_files",
                    "max_size_in_bytes" : 10737418240,
                    "max_files"         : 10,
                    "buffer_size"       : 0
                }
            },
            "extra" : {
              "DATABASE_NAME": "my_database_name"
            }
        }
    }
}
```

Yes, you can copy and paste this, and use it for your development environment.
Just make sure to alter any values that needs altering. Also remove any settings,
your application should not be using.

I'm quite certain for most of what's being set here, you'll find the use rather
obvious.

For the sake of completeness though, here's the same JSON structure, with its
entries set to the corresponding environment variable names discussed in:
[Configuration through environment variables](./through_environment_variables.md)

```json
{
    "instances": {
        "feeds_cats": {
            "lock_directory"  : "ECOENV_LOCK_DIR",
            "buffer_directory" : "ECOENV_BUFFER_DIR",
            "stats_keeper"    : {
               "gather_period"  : "ECOENV_STAT_GP",
               "history_length" : "ECOENV_STAT_HL"
            },
            "tcp" : {
               "host" : "HOST portion of: ECOENV_TCP_{uppercase application name}_{uppercase instance}",
               "port" : "PORT portion of: ECOENV_TCP_{uppercase application name}_{uppercase instance}"
            },
            "udp" : {
               "host" : "HOST portion of: ECOENV_UDP_{uppercase application name}_{uppercase instance}",
               "port" : "PORT portion of: ECOENV_UDP_{uppercase application name}_{uppercase instance}"
            },
            "uds" : {
               "directory"        : "Directory portion of: ECOENV_UDS_{uppercase application name}_{uppercase instance}",
               "socket_file_name" : "Base name portion of: ECOENV_UDS_{uppercase application name}_{uppercase instance}"
            },
            "logging"         : {
                "format"       : "ECOENV_LOG_FORMAT",
                "date_format"  : "ECOENV_LOG_DATE_FORMAT",
                "level"        : "ECOENV_LOG_LEVEL",
                "file_logging" : {
                    "directory"         : "ECOENV_LOG_DIR",
                    "max_size_in_bytes" : "ECOENV_LOG_MAX_SIZE",
                    "max_files"         : "ECOENV_LOG_MAX_FILES",
                    "buffer_size"       : "ECOENV_LOG_BUF_SIZE"
                }
            },
            "extra" : {
                "DATABASE_NAME": "ECOENV_EXTRA_MY_COOL_APPLICATION_FEEDS_CATS_DATABASE_NAME"
            }
        }
    }
}
```

YES! You can have multiple instance for an application, configured in one
configuration file.

Just put them under `"instances"` and make sure your instance identifier is the
key.

There you have it. Everything you need to know about configuration files as
used by Ecosystem.
