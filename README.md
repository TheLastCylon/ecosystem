# Ecosystem

A Python framework for creating message-based, distributed systems. Allowing for
TCP, UDP and UDS communications. Using JSON as the communications protocol.

## Features

- Multi-instancy, without the need for containerization.
- Real-time Telemetry, without the need for log-aggregation.
- Optional Distributed Tracking (Request Tracking), at protocol level, using UUIDs. 
- Queueing for both sending and receiving messages, without the need for
  installation or management of external queueing mechanisms.
- Configuration through both environment variables and config files, at three levels:
  - Machine/Container,
  - Application and
  - Instance
- Both transient and persisted clients for TCP and UDS. With configurable connection heartbeat.
- File Logging and log rotation, by default. Buffered file logging is optional and configurable.
  - Both log level and buffer size can be adjusted on the fly, while applications are running.
- Seamlessly use Ecosystem `senders`, clients and DTOs, from within [FastAPI](https://github.com/fastapi/fastapi)
  applications.

For more, take a look at the [documentation](https://github.com/TheLastCylon/ecosystem/blob/main/documentation/documentation_root.md) on GitHub.

## License

Ecosystem is developed under the BSD 3-Clause License.
