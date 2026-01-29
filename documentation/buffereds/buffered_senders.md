# Buffered senders, what they are for.

In the world of web-development, message retention isn't much of a concern. The
attitude towards it is lackluster at best, with the excuse that:

"The user will just re-submit."

In distributed systems however, it is a cardinal sin to lose a message.

In the case where a client needs the response from the server to continue
processing. One needs to have a failure process in place. In the case of
Ecosystem, you'll handle that where you invoke your `sender` functions from.

However, in the case where a client can be done with having a callback from a
server, or only needing to notify a server of something, `buffered_senders` are
the go-to solution.

Especially if you want the ability to reprocess messages, in the event that the
server becomes unavailable or unreachable for some reason.

They can also be used to do client side rate-limiting, by setting its `wait_period`.

They are also light-weight enough to use for any sending where you want to do
some kind of fire-and-forget message to a server.

Combined with a function decorated with `run_soon`, they even allow you to
do things like queue messages for sending, after the context of the function
you are in, has completed.

For an example of this, take a look at the `[router]` component of the
[Fun Factory example system](../examples/fun_factory/fun_factory.md).
