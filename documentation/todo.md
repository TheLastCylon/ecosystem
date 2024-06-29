# TODO

## For MVP
- [ ] Ecosystem JavaScript client

- [ ] Queued sender: delay between send attempts (user defined back-off function?)
- [ ] Queued sender: keeper
- [ ] Queued sender: queue manipulation handler

- [ ] Test Timeout on communications.
  - [ ] TCP communications
  - [ ] UDP communications.
  - [ ] UDS communications.

- [ ] Documentation: Handlers
- [ ] Documentation: Queued endpoints, remember pause and unpause
- [ ] Documentation: Application base
- [ ] Documentation: Application configuration
- [ ] Documentation: Logging

- [ ] Communications white-list. As in, only these people may talk to me! Yes, we are going with deny-by-default!

## Beyond MVP
- [ ] LRU cache

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
