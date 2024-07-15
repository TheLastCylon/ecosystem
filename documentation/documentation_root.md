# Ecosystem Documentation

---
Before you continue, allow me to answer a question I'm sure I'm going to get
quite often.

Why is the package name `ekosis`?

Well, it was supposed to be `ecosystem`, but apparently this is not allowed by
PyPi. So, I had to make a choice: Stick with the name I like for this, or
completely alter everything and break away from the name completely.

Well, I'm stubborn. So I stuck with it.

`ekosis` is an abbreviation of the word `Ekosisteem`, which is the Afrikaans word
for `Ecosystem`. The meaning of the two words are exactly the same. Afrikaans also
happens to be one of the two natural languages, I'm completely fluent in. I'm sure
you can guess what the other one is.

So yes. The project will continue to be known as Ecosystem, the package however,
will have the name `ekosis`.

---
## Installation

`pip install ekosis`

---
## Documentation
- [Requirements](./requirements.md)
- [Ecosystem on Windows](./ecosystem_on_windows.md)
- [Ecosystem on POSIX](./ecosystem_on_posix.md)
- [Examples (as in: Learn by example)](./examples.md)
- [Ecosystem application configuration](./configuration/configuration.md)
  - [Through environment variables](./configuration/through_environment_variables.md)
  - [Through configuration files](./configuration/through_configuration_files.md)
  - [Getting to the configuration, in code](./configuration/getting_config_from_code.md)
- [Statistics (Real-time Telemetry) made easy](./statistics_keeper.md)
  - [Real-Time Telemetry Example](./examples/telemetry/telemetry.md)
- Queues
  - [Understanding queues](queueds/understanding_queues.md)
  - [Questions and Answers](queueds/questions_and_answers.md)
  - [Queued Endpoints and Senders, the technical stuff](queueds/technical_stuff.md)
  - [Queued Endpoints, what they are for](queueds/queued_endpoints.md)
  - [Queued Senders, what they are for](queueds/queued_senders.md)
  - [Standard endpoints for queue management](queueds/standard_endpoints_for_management.md)
- [The Ecosystem command line tool](./command_line_tool.md)
- [Why do this?](./why.md)
- [TODO (as in: The stuff still pending)](./todo.md)
