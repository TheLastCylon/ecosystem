# TODO
- [ ] Timeout on TCP communications.
- [ ] Timeout on UDP communications.
- [ ] Timeout on UDS communications.
- [ ] running as daemon
- [ ] lru cache
- [ ] Documentation
  - [X] the protocol
  - [ ] Handlers
  - [ ] Queues
  - [ ] Application base
- Queueing
  - [ ] Incoming queue
    - [X] i.e. A queue that gets data in on one of the communication channels
    - [X] These will typically have a handler, that pops data off the queue, and does something with the data in the queue.
    - [ ] Pause for:
      - [ ] Accepting : Prevents new requests from going into the queue. Throws an error that is propagated to the client.
      - [ ] Processing: Just pauses processing. Still accepts new requests.
      - [ ] Both      : Stops accepting and processing
    - [X] Queues
      - [X] Incoming queue
      - [X] Error queue
  - [ ] Outgoing queue
    - [ ] A message of the: "Hey you, do your thing with this data, I'm done with it." kind.
    - [ ] This typically requires some kind of triple queue
      - [ ] one for the outgoing messages
      - [ ] one for messages that need to be retried
      - [ ] one for messages that have errored out

- [ ] standard handlers
  - [ ] For queued request handlers
    - [ ] move requests in error queue to incoming queue
      - [ ] for specific uid
      - [ ] for all
    - [ ] clear error queue (as in forget those request existed)
    - [ ] get queue sizes
      - [X] through standard statistics handler
      - [ ] through queue size specific handler
    - [ ] see a specific request in a queue, using the uid

- [ ] configuration
  - [ ] application name
  - [ ] host
  - [ ] port
  - [ ] client_request_timeout
  - [ ] logger
    - [ ] log file
    - [ ] log max size
      - [ ] 1024*1024*1024      = 1,073,741,824 i.e. One megabyte
      - [ ] (1024*1024*1024)*10 = 10,737,418,240 i.e. 10 mega-bytes

```json
{
  "applications": [
    {
      "name"           : "test_application_001",
      "host"           : "127.0.0.1",
      "request_timeout": 10,
      "logging": {
        "directory": "/asdf/asdf/asdf/asdf",
        "max_size_in_bytes": 10737418240,
        "max_files"        : 10
      },
      "instances": [
        {
          "id"             : 0,
          "host"           : "127.0.0.1",
          "port"           : 1000,
          "request_timeout": 10,
          "logging": {
            "directory": "/asdf/asdf/asdf/asdf",
            "max_size_in_bytes": 10737418240,
            "max_files"        : 10
          }
        }
      ]
    },
    {
      "name"           : "test_application_002",
      "host"           : "127.0.0.1",
      "request_timeout": 10,
      "logging": {
        "directory": "/asdf/asdf/asdf/asdf",
        "max_size_in_bytes": 10737418240
      },
      "instances": [
        {
          "number"         : 0,
          "host"           : "127.0.0.1",
          "port"           : 1000,
          "request_timeout": 10,
          "logging": {
            "directory": "/asdf/asdf/asdf/asdf",
            "max_size_in_bytes": 10737418240
          }
        }
      ]
    }
  ]
}
```


# Communication
## Request
```json
{
  "request": {
    "name": "asdfasdfasdf",
    "data": {
    }
  }
}
```

## Response
### success
```json
{
  "response": {
    "status"       : 0,
    "data"         : {
    }
  }
}
```

### failure
```json
{
  "response": {
    "status"       : ">0",
    "error-message": ""
  }
}
```
