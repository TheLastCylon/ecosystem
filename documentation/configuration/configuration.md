# Configuring an Ecosystem application

There are three ways in which one can effect configuration of an Ecosystem application.
1. Programmatically hard-code values in the application.
   1. For anything other than example code: This is BAD PRACTICE! DON'T DO IT!
2. Through a JSON format configuration file.
   1. This is good for your development environment.
   2. However, for security reasons: DON'T DO THIS IN A PRODUCTION ENVIRONMENT!
   3. Configuration files should not even be part of your code repository!
   4. Adjust your `.gitignore` settings to make sure any configuration files you are using, are ignored. This will ensure you don't accidentally add them to your repository.
3. Through environment variables.
   1. This is what you want to use in your production environments!

Before we continue into how to do the above though, we need to have a word about:
1. Your application name.
2. Running instances of your application.

Here we go ...

---
## Your application name (!!! THIS IS IMPORTANT !!!)

Ecosystem is not just about creating a single service, that runs alone on one computer somewhere.

The name kind of gives its purpose away: EcoSYSTEM!

If all you want to do is write one service, that runs on one instance of a cloud server somewhere, Ecosystem will do that for you, rather neatly.

However, the problem it is designed to solve, is orders of magnitude bigger than that.

So, a couple of standards absolutely have to be put into place, your application name is one of them. 


Within the context of Ecosystem, your application name is:
- the basename portion of `sys.argv[0]`
- stripped of the `.py` extension
- converted to snake-case
- converted to lowercase.

That means:

If you have a script: `/SomeLongPath/MyProjectDirectory/MyCoolApplication.py`

When you run that script, the application name is: `my_cool_application`

Of course, if the script file name is already `my_cool_application.py`, the application name is still `my_cool_application`

This becomes important when you begin to run multiple Ecosystem applications on the same machine.
It's even more important when you begin to run multiple instances, of the same Ecosystem application, on one machine.

It also effects things from configuration, all the way through to your code repository.
Because you simply **can not** have a situation where all your applications reside in files named `server.py`.
Even if your various project directory structures allows for that, come run-time in production, your system simply won't work.

So, name your application scripts uniquely and neatly, throughout all your Ecosystem code repositories!

---
## Running instances

Every time you run an Ecosystem application, you absolutely have to specify an identifier, that indicates how you want to identify the running instance of the script you are about to start.

This is done with the `-i` or `--instance` command line options.

When you start an Ecosystem application, one of the first things it does, is to make sure that there isn't an instance of itself running already.
If there is, the one you are trying to start will inform you of the fact, and then exit.

Ecosystem applications, can be configured down to running-instance-level.

So, an application named `my_cool_application` can be configured very differently for an instance identified with `feeds_cats`, than an instance identified with `feeds_dogs`

The level of configurability you have with Ecosystem, without having to write a single line of code, is way beyond anything I've seen with any other framework.

Yes. I know. You're welcome. It's my pleasure, I assure you.

Think about it: I did not create Ecosystem in a vacuum. I was the first Ecosystem user, even before it was named Ecosystem, I was using it.

These features exist, because I needed them. I'm rather certain others need them too.

Now, let's move on and look at how one does all this configuration.

First, let's look at [using environment variables](./through_environment_variables.md).
