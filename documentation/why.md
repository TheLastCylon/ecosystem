# Why did I do this?

## The short answer:
I got irritated.

## The medium answer:
Some time on 4 June 2024, I got irritated enough to start on this. At the time of writing this answer, it is 18 June 2024.
Less than a month of part-time effort, and I'm already at a point where I have something usable.

Somehow, the fact that one person can go from having nothing, to having this kind of solution in less than a month of effort, irritates me even more.

## The long answer:
### What about the little guy?
The I.T. industry has become so used to using carrier-grade solutions, for swatting flies, that it's damn near impossible to have a successful start-up without the monetary backup of some billionaire or another.

Seriously!

When I need a simple, no-frills message-broker:
1. Why should I become a Redis/Kubernetes/RabbitMq/AWS/Azure expert?
1. Why should I require my client to pay for a bazooka, when the problem can be solved with a rolled-up copy of their local tabloid?

As an industry, we have become so obsessed with the big guys, that we completely forgot about the millions of little people out there.

It is my hope that Ecosystem will help a few of the small people to get what they need, rather than what the industry dictates they should have.

### HTTP and HTTPS
Why, in the name of all things good and holy, does all network communications now seem to happen using HTTP or HTTPS?

Really! Why?

Every single framework I've seen, wither it targets front-end, back-end or both, uses HTTP.

WHY!?

None of the solutions I've had to do in these frameworks, factually needed HTTP. Everything ends up being JSON wrapped inside HTTP anyway.

And right about now I can hear a whole host of developers out there saying: "But HTTPS is secure, we use HTTPS because it's secure."

At this I'll sag my head and bemoan the state of education in our industry. If you were one of the ones wanting to say that, please take the time to learn about TCP, SSL/TLS and try to understand:

1. HTTPS is nothing more than HTTP, transmitted on a TCP connection, secured with SSL/TLS.
1. Any TCP connection can be secured with SSL/TLS. Even UDP can be secured with DTLS!

Thing is, even this is a non-concern, because anything you write with a modern back-end framework, is basically guaranteed to be hiding behind either an Apache or Nginx service.

These are the tools that make sure the outside world can only speak to your back-end, using secured connections.
They also take care of things like load balancing.

So, as long as a web-application running inside a browser, knows how to make a secure TCP connection, speaking a protocol that your back-end understands ... All is golden.

What's more though is: It's not as if this is a secret. It's in the names: HTTP and HTML.

- HTTP is Hypertext Transfer Protocol. A protocol designed for transferring Hypertext between machines on a network!
- HTML is Hypertext Markup Language. A language browsers use in order to render what you see in the browser.

Given that we are now in a world where we are NOT transferring static HTML data to web-browsers anymore: Why are we still using HTTP?

Why can't I just have a TCP server, sitting behind Apache or Nginx?

So what's the point of using HTTP in this fantastic, modern world of ours?

Why can't we just use JSON as a protocol and get it over with?!

### TCP? Why not UDP or UDS?
In modern day terms TCP is an absolute requirement for web-applications! Thing is, not all back-ends are exposed to the internet.

There are times when I need a back-end to NOT be exposed to the internet at all. And what's more is: There are times when I need a back-end to be oblivious of the fact that the internet even exists.

Yes, there are times when I need a back-end, that does not talk to a browser, ever.

Amazing, right?

NO!

This is how we did stuff way back when browsers were hardly able to render an HTML page!

There is nothing amazing or complicated about this.

This use-case still exists! Just ask anyone who has had to create a trading platform.

So ... Again ... Why does every back-end framework I've come across, either only support HTTP over TCP, or finding the documentation on using its UDP features is nearly impossible?

Why can't I have a framework that also supports UDP, or even better, UDS?

In fact: Why can't I have all of the above? What possible reason is there that I should live in a world limited to only one communications protocol?

## Rant over ... for now.
Ecosystem, is my attempt at addressing the things I mention above, and quite a bit more.

No, it's not perfect!

I can't hope to contend with the likes of NestJS, Django, Laravel or any of those solutions.

I'm just one person, and there are only so many hours in any given day.

But ... Maybe ... Just maybe ... There are people out there who happen to agree with me, or perhaps even people who find what I've done here useful.
