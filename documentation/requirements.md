# Requirements
| Requirement                                    | Version    |
|------------------------------------------------|------------|
| [python](https://www.python.org/)              | \>= 3.11.4 |
| [sqlalchemy](https://sqlalchemy.org)           | \>= 2.0.31 |
| [pydantic](https://docs.pydantic.dev/latest/)  | \>= 2.8.2  |


## Python
Yup, you will need Python for this.

Ecosystem might work with lower versions, but the probability of that is very
low, primarily due to my use of asyncio.

As much as I love to lose my cool with Python and the world of dynamic and duck
typing, it is a damn good solution to a world-wide problem.

To the people working on bringing Python to the world, you are pretty damn
awesome! I dislike many of the PEP coding guidelines, so I tend to ignore them.
But the solution as a whole ... Love it! Just love it!

Just one thing ... What's up with the name mangling of class members that start
with double underscore? That one had me baffled for a while.

## SqlAlchemy
All the queue solutions in Ecosystem, rely on [SqlAlchemy](https://sqlalchemy.org)
and [Sqlite](https://sqlite.org).

I tested with version 2.0.31, lower versions might work though. Let me know if
they do, and I'll start a list of what works and what does not.

Side note: The people doing [SqlAlchemy](https://sqlalchemy.org) and
[Sqlite](https://sqlite.org) do not get the credit they deserve. Both these
solutions are pretty damn amazing. So, from me to all the people involved with
these: Thank you. You Rock!

## Pydantic
I tested with version 2.8.2, lower versions might work but do keep in mind that
it's untested.

Also: Without [Pydantic](https://docs.pydantic.dev/latest/), Ecosystem would
have required alot more work than it has so far.

Here too, I honestly don't think the people working on
[Pydantic](https://docs.pydantic.dev/latest/) as a solution, get enough credit
for what they have achieved. Thank you. All of you. You Rock Too!
