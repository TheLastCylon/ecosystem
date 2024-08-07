# Queued endpoints, what they are for.

---
## What they are for.

It doesn't happen often in the context of web-development. But with distributed
systems, there are often cases where you want your application to be able to
receive messages as fast as possible, and process them when there is time to do
so.

Of course, in terms of computing, one second is a rather long time. So it might
be better to explain this with a less abstract example:

---
### Stamping the papers

Imagine a factory worker, who's responsible for adding a stamp on a sheet of paper.

There is a metal box, labeled "pending", where sheets of paper needing to be stamped,
arrive. When there are sheets in that box, a conveyer system grabs them and gives
them to the worker, one at a time.

The worker does not know how the sheets of paper arrive, nor even why. All they
know is:
- When there is a sheet of paper in front of them, they need to put a stamp on it.
- If something went wrong with the stamping of the paper, they need to put the
  paper in a box labeled "False"
- Otherwise, they put it in a box labeled "True"
- Sometimes, there's hardly ever a paper that needs to be stamped.
- Other times, they come one after the other, for days on end.

What the worker does not know is:
- There's a whole production line involved in manufacturing the paper they stamp.
- This is a mass production effort, that often gets blocked due to supply issues.
- The transportation of produced paper is costly, and is therefore done in bulk.
- The paper they place in the box labeled "True", gets sent to a customer.
- The paper they place in the box labeled "False", gets recycled. Eventually
  ending up in front of the worker again, as a clean sheet of paper.

The metal box labeled "pending", is just a buffer. Giving the worker the
freedom to focus on one sheet of paper at a time, and do the job of stamping,
to the highest standard possible.

The analogy isn't perfect, but: A function you decorate with `queued_endpoint`,
is in effect: The worker that stamps the sheets of paper.

### So how do they fit into a business then?
Examine this whole scenario from the perspective of the factory owner,
and things become a bit more clear.

The factory owner, i.e. the business that owns the system, isn't going to employ
thousands of people for 2 seconds each, all at the same time, to have each one
stamp a single sheet of paper. It would be a logistical nightmare and nearly
impossible to sustain. And that's not even considering the human resources
complaints. Or politics of having to hire and fire thousands of workers every
day.

This, is the computing equivalent of:

NOT bothering with load-balancing, because the messages being received, do NOT
need immediate, processed-responses.

That translates to:

When an immediate, processed-response isn't required, queueing incoming requests
in the service that has to deal with them, is a cost-effective alternative to
load-balancing.

Keep in mind:

From the perspective of a computer, the phrase "immediate processed-response",
means something has to happen in the order of milliseconds, and the result of
that something has to be reported back to the thing that made the request.

So, if a client process can get on with doing things while it waits for a
call-back from a service. Or, if the result of a procedure gets sent to another
service, there is an opportunity to use a queueing mechanism, that could save
you money in the long run.

This is where a `queued_endpoint` fits into the overall architecture, of a system.

Ecosystem's queued endpoints, are also a middle ground solution, for when you
don't have enough load, for long enough, to justify paying for another kind of
queueing solution.

They can also serve as a stop-gap measure, for when you have to have a queueing
solution right now, but have to wait for it to be put in place.
