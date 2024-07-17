# Ecosystem

A Python framework for creating message-based, distributed systems. Allowing for
TCP, UDP and UDS communications. Using JSON as the communications protocol.

**Please note**:

Ecosystem does not do HTTP communications. It is first and foremost intended to
**not** be used with HTTP.

Although it can be used as one, it is **not** a web-development back-end framework.

The problem being solved by Ecosystem, is orders of magnitude bigger than the
creation of a web-site.

As such, the "out-of-the-box" features include:

- Multi-instancy, without the need for containerization.
- Real-time Telemetry, without the need for log-aggregation.
- Optional Distributed Tracking (Request Tracking), at protocol level, using UUIDs. 
- Queueing for both sending and receiving messages, without the need for
  installation or management of external queueing mechanisms.
- Configuration through both environment variables and config files, at three levels:
  - Machine/Container,
  - Application and
  - Instance
- File Logging and log rotation, by default. Buffered file logging is optional and configurable.

For more, take a look at the [documentation](https://github.com/TheLastCylon/ecosystem/blob/main/documentation/documentation_root.md) on GitHub.

## License

Ecosystem is developed under the BSD 3-Clause License.
