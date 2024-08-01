# How does Ecosystem compare to something like ZeroMQ?

ZeroMQ is a library. Ecosystem is a framework. The two can't really be compared.

At best, one can say they solve related problems, from two different fronts.

As a framework, Ecosystem is created in Python, so it can only really be used
with Python.

ZeroMQ can be used with a whole host of languages. But it lacks features that
Ecosystem has out-of-the-box. Real time telemetry, and Distributed message
tracking are just two examples of this.

Ecosystem is intended to make the activity of creating components for a
distributed system: Easy, fast and with as little code as possible. So it
abstracts things like having to create sockets, away from the developer.

The framework solves the problem of TCP, UDP and UDS communications, just like
ZeroMQ. It provides message queuing in much the way ZeroMQ would. But with
Ecosystem, the amount of code you have to write to achieve this, is virtually
nothing.

For instance, in order to have a queued sender, you need about `5` lines of code.
Nothing more. No installing extra stuff, no running an external service. Just
code.

It currently lacks ready-made solution for pub/sub message brokering. It is
intended to have those solutions though. And it is already remarkably easy to
create a custom message broker, using the Ecosystem framework.

But part of the design intent behind Ecosystem, is also to enable system
architecture, that can avoid pub/sub mechanisms.

Ecosystem is not intended to replace any of the industry standardised queuing or
caching mechanisms. It is geared more towards making it **economical**, to have
distributed systems.

Take a look at the [Fun Factory](examples/fun_factory/fun_factory.md) and
[Proper Fun](examples/proper_fun.md) system examples.

With the use of Ecosystem the [Proper Fun](examples/proper_fun.md) example, is
an entire system, with `7` servers and `1` client, that includes queuing,
telemetry, distributed message tracking, etc, etc, etc. ... With only `476` lines
of code required ... For the ENTIRE system.

Also, Ecosystem applications can be re-configured to use UDP, rather than TCP,
with nothing more than an environment variable. In fact, an Ecosystem application
can have any combination of a TCP, UDP or UDS listener, all at the same time.
And requires nothing more than environment variables to have that. As in: You
don't have to write code for it at all.

The entire framework relies heavily on Python's asyncio, and abstracts it away for
the user. So you can have all the benefit of asyncio, without having to wrap your
head around it first.

Again though, take a look at the examples.

I am quite certain you'll find that ZeroMQ and Ecosystem solve related problems.

Each have their advantages and disadvantages.

But, if you need to put down a sane distributed system within 30 days.
You'll have a rough time making that happen with ZeroMQ.

With Ecosystem, even in its current Beta state, you could pull it off.
There will likely be some late nights and over time, but you'll have a reasonable
chance. This, while also having all the bells and whistles required for a
distributed system, ready-made and in place.

Also keep in mind, as a technology, ZeroMQ is mature.

Ecosystem was started on the 4th of July 2024. The first commit to GitHub
happened on the 19th of July 2024.

Yes, it is remarkably usable, fast and easy to learn. For a project this
young, I'm kind of mind-blown at what it is capable of already.
But, it does not even have proper tests yet.

Yes, I'm personally happy to use it in a production environment. But that's
because I created it and can make changes and apply fixes on the fly. Another
person would not have that luxury.

If you intend to suggest Ecosystem for a live production system: Proceed with
caution. Understand what you'll need and what your time-lines are, before jumping
the gun and using Ecosystem in its current state.
