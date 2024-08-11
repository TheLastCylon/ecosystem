# Transient, vs persisted clients.

TCP (Transfer Control Protocol) and UDS (Unix Domain Sockets) are
connection-based protocols, in contrast UDP (User Datagram Protocol) is
connectionless.

This is part of the reason why UDP tends to outperform TCP and UDS in terms of
speed in many cases.

It is **not** always true, that UDP is faster than TCP and UDS though.

There are conditions, under which TCP and UDS can approach and even outperform
UDP.

This is why Ecosystem allows for **Transient** and **Persisted** clients,
for both TCP and UDS.

## Transient clients

A **transient** client, is one where the connection is opened right before a
message is sent, and then closed the moment after a response has been received.
This is the typical type of TCP connection. There are good reasons for needing
this kind of client. In the web-development world this is typical, because one
simply does not know how many clients will attempt to be connected at the same
time.

But due to the opening and closing of connections, it is significantly slower
than UDP.

## Persisted clients

Then there are **persisted** clients. With these clients, the connection is made
on the first message sent, and kept open for the life-time of the client. Even
if the server closes the connection, these clients will try to regain the
connection on a regular basis. The point being that, with not having to open
and close the connection with each message, a gain in terms of throughput is
achieved.

Under these conditions, TCP tends to give 96% of the throughput that UDP does.
UDS on the other hand, outperforms UDP, to the tune of about 108% the throughput
of UDP.

With UDS, the downside is ofcourse, that your client and server has to run
on the same machine.

## Conclusion
If you have a finite number of clients, that you control, connecting to an
Ecosystem application. Using persisted TCP or UDS connections, will likely
give you a performance boost.

If your clients run on the same machine as your Ecosystem application, UDS
persisted clients, will consistently outperform UDP.

Consider your needs and architecture carefully. There are likely performance
boosts you can get, by doing nothing other than making sure you use the
right type of client for the job at hand.
