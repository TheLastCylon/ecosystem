# Getting your applications configuration in code

Ecosystem's `AppConfiguration` class is implemented as a singleton.

You can import it anywhere in your code:

```python
from ekosis.configuration.config_models import AppConfiguration
```

And get an instance of it with:

```python
config = AppConfiguration()
```

From there, you can get to the various configurations.

```python
    config.name
    config.instance
    config.tcp
    config.udp
    config.uds
    config.stats_keeper
    config.logging
    config.lock_directory
    config.queue_directory
```

The only thing of note here is: The extra settings.

As discussed in [configuration through environment variables](./through_environment_variables.md).
You can get Ecosystem to retrieve settings that have nothing to do with Ecosystem.

The `extra` attribute of `AppConfiguration()`, is a dictionary with strings as keys and values.

So, once more, that means:
1. For an application named: `my_cool_application`
2. Being run as instance: `feeds_cats`
3. Where an environment variable named `ECOENV_EXTRA_MY_COOL_APPLICATION_FEEDS_CATS_DATABASE_NAME` has been created.
4. There will, in the instance configuration available in your application at runtime, be an entry named `DATABASE_NAME`, that has been set to the value of `ECOENV_EXTRA_MY_COOL_APPLICATION_FEEDS_CATS_DATABASE_NAME`

You can get the value of that environment variable with:

```python
from ekosis.configuration.config_models import AppConfiguration

config=AppConfiguration()

if "DATABASE_NAME" not in config.extra.keys():  # Remember to check that the entry is actually there.
    raise Exception("Database name not configured!")

database_name=config.extra["DATABASE_NAME"]  # And here you can get the value.
```

One last thing:

Ecosystem will do nothing with values set after the call to the `ApplicationBase` `__init__` method.

Trying to programmatically effect settings after your application has done that, is quite pointless.

Also:

Yes, you can abuse the `extra` attribute into being an application wide variables store.

I'm not saying don't do it, it can be very useful for that, just remember:
1. Be responsible!
2. Be accountable!
3. Keep your code sane!
