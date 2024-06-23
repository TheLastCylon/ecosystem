# TODO
- [ ] Prevent startup of duplicate instances.

- [ ] Cater for Windows OS in all default configurations

- [ ] Ecosystem JavaScript client

- [ ] Test Timeout on communications.
  - [ ] TCP communications
  - [ ] UDP communications.
  - [ ] UDS communications.

- [ ] LRU cache

- [ ] Documentation: Handlers
- [ ] Documentation: Queued endpoints, remember pause and unpause
- [ ] Documentation: Application base
- [ ] Documentation: Logging
- [ ] Documentation: Application configuration

- [ ] Queueing

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

  - [ ] Outgoing queue i.e. Queued sender
    - [ ] A message of the: "Hey you, do your thing with this data, I'm done with it." kind.
    - [ ] This typically requires some kind of triple queue
      - [ ] one for the outgoing messages
      - [ ] one for messages that need to be retried
      - [ ] one for messages that have errored out

- [ ] Proper handling of error responses in clients. i.e. When a client gets an error response rather than the expected response DTO.


- [ ] standard endpoints
  - [ ] Stop: As in a handler that will tell an application to shut down


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

# Possibly won't do:
- [ ] Running as a daemon:
  - NOTE: This Likely won't get done due to lack of standard mechanisms for achieving this in a cross-platform way.
  - Python's multiprocessing does not do true Unix daemon running and solutions like python-daemon are platform specific.

