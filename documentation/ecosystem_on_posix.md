# Ecosystem on POSIX

Due to possible permission issues the default locations are as follows:

| purpose                  | default location | what it should be |
|--------------------------|------------------|-------------------|
| log files                | `/tmp`           | `/var/log`        |
| lock files               | `/tmp`           | `/run`            |
| Unix Domain Socket Files | `/tmp`           | `/run`            |

The location for the sqlite database files used for queues, has to be explicitly set, on all platforms.

