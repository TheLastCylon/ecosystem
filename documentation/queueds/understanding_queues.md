# Understanding queues.

Right now, there are two types of queues you can use in Ecosystem. They are
rather basic in terms of what they do, but they satisfy the 80% use case with
respect to queueing. Of course, this will be expanded on as development
continues. Current plans include things like:
- Ordered sending and receiving,
- Broadcasting to multiple servers, and
- Ordered Broadcasting.

And no, you do not have to install anything with respect to external queue
mechanisms. All queueing solutions provided by Ecosystem, are done within the
framework.

Unlike some queueing solutions, you do not have to write any code that polls to
check if there's anything in the queue either. Ecosystem invokes the functions
you decorate with `queued_endpoint` or `queued_sender` for you.

What is important though, is to understand:
1. When to use either `queued_endpoint` or `queued_sender`
2. How far you can push their use.

Before we look at `queued_endpoint` and `queued_sender`, lets first look at
how far you can push their use.

---
## How far can you push Ecosystem's queueing

This is dependant upon your hardware and quite a bit more upon your file system.

Ecosystem uses [Sqlite](https://sqlite.org) in combination with
[SqlAlchemy](https://sqlalchemy.org), for creation and management of the queue
databases.

Both `queued_endpoint` and `queued_sender` cause the creation of two (2) [Sqlite](https://sqlite.org)
databases:
- One for messages that are pending, aptly named `pending` and
- one for messages that have failed, named  `error`

Each database has only one table. This table has:
- Three fields.
- Two are indexed.
- One being a big-int, that serves as the primary key and is auto-incremented.
- The other being a 16-byte representation of a UUID.
- The third field is a string, that can be of any size.

The string is where message data is stored, in the form of a JSON string.

The UUID field is used to store the UUIDs of a message, making each one
accessible through its UUID.

Yes, this is exactly the protocol level UUID that an Ecosystem client creates,
when you use either `sender` or `queued_sender`.

Yes, you can take control of the UUID used, from within your code.

This can be rather important for when you want to debug things, and need to look
at entries in a queue's error database.

Moving on to answering the question at hand though:

The theoretical limit of sqlite databases, is in the order of 140 terabytes. So,
the limitations of how far you can push Ecosystem's queues is genuinely dependent
on your hardware, and file system.

A lot can also depend on how much RAM you have available. As it's entirely
possible to configure things in such a way, that your queue databases aren't
written to disk, until the application shuts down.

Yes, If you aren't afraid of losing messages due to some kind of system
catastropy, all your queue databases could live in RAM.

Now that you know all this, let us move on and take a look at
[answering some basic questions](questions_and_answers.md).
