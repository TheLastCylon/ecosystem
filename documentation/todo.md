# TODO

## For MVP

- [ ] Middleware!

- [ ] Observability with Open Telemetry evolution.
  - [ ] Python example for use with `pushgateway` --> `Prometheus` --> `Grafana`
  - [ ] Logging into log aggregation tools like `Loki`, through `Promtail`.
  - [ ] Open telemetry example with exporters for traces. (e.g. Jaeger exporter)
  - [ ] Setting up `Grafana` to use the observability stack of choice.

- [ ] Documentation: LRU Cache
- [ ] Example: LRU Cache

- [ ] Improve Queued senders to use error keeper when a server is unreachable.
  - This will make Queued senders unusable outside Ecosystem, is this what we want?

- [ ] Benchmarking: queues.

- [ ] Example: Project structure
- [ ] Example: Project with Postgres database
- [ ] Example: Doing database migrations

- [ ] Documentation: The error keeper, why it exists and how to use it.
  - Example: a service needing to be communicated to goes down.
  - Setting of the error state when that happens.
  - Clearing of the error state when it is resolved.

## Beyond MVP

- [ ] Ecosystem Node.js client


- [ ] Sequenced Queued Sender
  - As in: Make sure messages groups are sent in order


- [ ] Broadcaster
  - As in: Send this message to a list of clients
  - Using a map of clients to route_key, where the route_key is that of what the servers should receive the message on.


- [ ] Sequenced Broadcaster

# Done
- [X] Make communication channels optional
  - [X] TCP
  - [X] UDP
  - [X] UDS
- [X] Command line argument parsing.
- [X] configuration through environment variables
- [X] configuration through json file
- [X] Documentation: the protocol
- [X] Documentation: Base example
- [X] Echo sever example
- [X] Documentation: Echo sever example
- [X] Echo client example
- [X] Documentation: Echo client example
- [X] Proper handling of error responses in clients. i.e. When a client gets an error response rather than the expected response DTO.
- [X] Queueing
  - [X] Incoming queue
    - [X] i.e. A queue that gets data in on one of the communication channels
    - [X] These will typically have a handler, that pops data off the queue, and does something with the data in the queue.
    - [X] Pause for:
      - [X] Accepting : Prevents new requests from going into the queue. Throws an error that is propagated to the client.
      - [X] Processing: Just pauses processing. Still accepts new requests.
      - [X] Both      : Stops accepting and processing
    - [X] Queues
      - [X] Incoming queue
      - [X] Error queue
  - [X] For queued endpoints
    - [X] move requests in error queue to incoming queue (i.e. re-process)
      - [X] for all
      - [X] for specific uid
    - [X] clear error queue: one with uuid (as in forget that request existed) (is popping a request off the error queue, so is done)
    - [X] clear error queue: all (as in forget all those request existed)
    - [X] get queue sizes
      - [X] through standard statistics handler
      - [X] through queue size specific handler
    - [X] inspect a specific request in an error queue, using the uid
    - [X] pop a specific request in an error queue, using the uid
  - [X] Outgoing queue i.e. Queued sender
    - [X] A message of the: "Hey you, do your thing with this data, I'm done with it." kind.
    - [X] This typically requires some kind of triple queue
      - [X] one for the outgoing messages
      - [X] one for messages that need to be retried
      - [X] one for messages that have errored out
- [X] Prevent startup of duplicate instances.
- [X] Update examples to run in context 
- [X] Make queues shutdown safe.
- [X] Documentation: Example fixes for running in Python context
- [X] Queued handler: Make sure it starts running at startup.
- [X] Documentation: Dice roller example
  - [X] Server
    - [X] guess endpoint
    - [X] roll endpoint
    - [X] roll_times endpoint
  - [X] Client
- [X] Documentation: sender
- [X] Documentation: Application configuration
  - [X] using environment variables
  - [X] using configuration files
- [X] Documentation: Handlers
- [X] Documentation: Application base
- [X] Documentation: Logging
- [X] Documentation: The statistics keeper, why it exists and how to use it.
- [X] Documentation: Accessing configuration in code.
- [X] Ecosystem command line tool
- [X] Queued sender: keeper
- [X] Queued sender: queue manipulation handler
- [X] enhance stats keeper to report on queued senders
- [X] create standard endpoints for managing send queues
- [X] improve command line tool for doing the management of send queues
- [X] Queued sender: delay between send attempts (user defined back-off function?) i.e. Rate limiting
- [X] Test Timeout on communications.
  - [X] TCP communications
  - [X] UDP communications.
  - [X] UDS communications.
- [X] Documentation: Queued senders
- [X] Documentation: Taking control of, and using UUIDs, used in the protocol
- [X] Documentation: The run_soon decorator. I LOVE PYTHON DECORATORS!!!
- [X] Documentation: The Fun Factory example
- [X] Make a Queued sender example.
- [X] RRD Graphing Tool example.
- [X] Documentation: Queued endpoints
  - [X] max uncommited
  - [X] max retries
  - [X] manipulation through standard endpoints and the queued handler keeper
- [X] Get Ecosystem ready for PyPI. Yes, we are that close.
- [X] p99 and p95 percentiles for endpoints
- [X] Persistent client connections
  - As in, clients connect once and don't close the connection until shut down or having to re-connect for some reason.
- [X] Improve persisted TCP and UDS clients to do connection heartbeat.
  - [X] Make heartbeat time configurable
- [X] Improve Queued endpoints to use `task.done` rather than flags to check if processes are running.
- [X] Command line tool: Rework into separate tools for telemetry, queued endpoint, queued sender and error states.
- [X] Documentation: Explain p99 and p95 statistics.
- [X] Logging adjustment on the fly.
  - i.e. Log Keeper?
  - Adjust log level
  - Adjust log buffer?
- [X] Tests.
  - end-to-end tests
    - [X] Does the application start up
    - [X] Does starting up an application for an instance that is already running, not start up.
    - [X] Can clients talk to servers.
      - [X] TCP
        - [X] transient
        - [X] persisted
      - [X] UDS
        - [X] transient
        - [X] persisted
      - [X] UDP
    - [X] senders
    - [X] queued senders
    - [X] endpoints
    - [X] queued endpoints
    - [X] do expected standard endpoints exist.
- [X] See if we can use Ecosystem `senders` from within a FastAPI application.
  - YES WE CAN!!!
- [X] Documentation: Persisted TCP and UDS clients
- [X] Example: Ecosystem + FastAPI 
- [X] LRU cache

# Possibly won't do:

# Won't do:
- [ ] Running as a daemon:
  - WHY:
    - This won't get done due to lack of standard mechanisms for achieving this in a cross-platform way.
    - Python's multiprocessing does not do true Unix daemon running and solutions like python-daemon are platform specific.
- [ ] Cater for Windows OS in all default configurations
  - WHY:
    - No sane, platform independent defaults exist!
- [ ] standard endpoints
  - [ ] Stop: As in a handler that will tell an application to shut down
  - WHY:
    - This is done through interrupt handling already.
    - It might get re-visited if remote shut-down of an application becomes a requirement.
- [ ] Communications white-list. As in, only these people may talk to me! Yes, we are going with deny-by-default!
  - Already partially dealt with, TCP and UDP connections are configured to listen on a host.
    - The host listened on, can be adjusted to do filtering already.
  - UDS connections can only be done on the same machine, so that is filtered by default.
  - Endpoint channel limitation. i.e. An endpoint may only be used on a list of [`tcp`, `udp`, `uds`] channels.
  - WHY:
    - As nice an idea as it is, it's kind of pointless.
    - If a malicious party can get on to one's network and freely make requests to Ecosystem applications,
      the failure point isn't Ecosystem, its network, firewall and system administration related.

# Ideas that might not see the light of day.

- For `queued_endpoints`.
  - Make max uncommited an environment variable.
    - Should it be?
    - We have `extra` for use by developers, should that not rather be used?
  - Create a standard `endpoint` that allows for setting of `max_uncommited` on the fly?


