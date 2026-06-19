# ekosis-log-shipper

A small, dependency-light C++ binary that tails EcoSystem log files and ships them to any
OTLP/HTTP+JSON-compatible logs endpoint (Loki, VictoriaLogs, etc.).

It exists as a deliberate alternative to running a full agent like Grafana Alloy
(300MB+) just to ship logs. `ekosis-log-shipper` is a single ~960KB binary with no
runtime beyond glibc, libcurl, and SQLite. Created for use in hardware constrained
environments like the Pi 1 Model B, while being able to function at scale.

---

## What it does

1. Watches a directory for `*.log` files (`inotify`, plus a defensive periodic re-scan so a
   missed event or a newly-started app's log file is never permanently skipped).
2. Tails each file, tracking position by **inode** (not path) so log rotation
   is survived with no lost or duplicated lines. The old file descriptor stays
   attached to the renamed file regardless of its current name; the shipper drains it to EOF
   before switching to the freshly-opened file at the path.
3. Reads each EcoSystem log line as an `OtlpLogRecord` JSON object (see
   `ekosis/data_transfer_objects/otlp_log_record.py` and `ekosis/logs/otlp_formatter.py`.
   This is the *mandatory* log format every EcoSystem app now writes), and wraps a batch of
   them into one OTLP/HTTP+JSON logs payload (`resourceLogs` -> `scopeLogs` -> `logRecords`).
4. POSTs that payload to the configured OTLP logs endpoint via libcurl.
5. Persists `(path, inode, offset)` per watched file in a small SQLite database, so a restart
   resumes exactly where it left off.
6. On a failed POST, the same batch is retried on the next tick.

Service identity (`service.name`/`service.instance.id` on the OTLP Resource) is pulled from
each line's own `attributes.application_name`/`attributes.application_instance` fields,
not parsed out of the filename. Those attributes are already on every line because
`OtlpFormatter` puts them there for a human directly rading the raw file with no
observability stack running.

---

## Linux-only

Please note, this utility will not work on Windows or Mac.

`inotify`, `st_ino`/POSIX `stat`, and `<dirent.h>` are all Linux-specific.
This will be revisited in the future to support Windows/Mac, if such requirements
show up.

---

## Building

### Dependencies

```bash
sudo apt install libsqlite3-dev libsqlitecpp-dev nlohmann-json3-dev libcurl4-openssl-dev
```

CMake 3.28+, a C++20 compiler (developed against gcc 13.3).

### Build

```bash
mkdir build && cd build
cmake ..
make
ctest   # runs the rotation-survival test
```

Produces the `ekosis_log_shipper` binary, plus `libekosis_log_shipper_lib.a` (the testable
core, linked into both the binary and `tests/manual_rotation_check`).

---

## Running

```bash
ekosis_log_shipper <watch_directory> <otlp_logs_endpoint> <state_db_path>
```

Example:

```bash
ekosis_log_shipper /tmp/observable_fun http://optiplexer.local:3100/otlp/v1/logs /var/lib/ekosis_log_shipper/state.sqlite
```

- `<watch_directory>`: directory containing the EcoSystem apps' `*.log` files.
  (`ECOENV_LOG_DIR` in your app's start script).
- `<otlp_logs_endpoint>`: an OTLP/HTTP+JSON logs endpoint. For Loki, this is
  `http://<HOST>:3100/otlp/v1/logs`, **not** `/loki/api/v1/push` (that's Loki's native
  push API and expects a different payload shape entirely).
- `<state_db_path>`: path to the SQLite file used for crash/restart recovery. Created if it
  doesn't exist.

No config file, no flags, no branching on log content, the envelope wrap is fixed and
mechanical by design.

---

## Loki-specific note: structured metadata vs. labels

If you're shipping straight to Loki's OTLP endpoint (bypassing Alloy entirely), be aware of a
real Loki constraint:

`limits_config.otlp_config`'s `action: index_label` only applies to
**Resource** attributes like `service.name` and `service.instance.id`.

Per-line attributes like `severity_text` can only land as `structured_metadata`, never as an indexed label, when going
in via Loki's native OTLP ingestion path, there's no equivalent of Alloy's `stage.labels`
hook on this path. `severity_text` is still fully queryable via LogQL
(`| severity_text="ERROR"`), it just won't appear in Grafana's Label browser dropdown.

Loki also needs `allow_structured_metadata: true` and the `tsdb`/`v13` schema (not
`boltdb-shipper`/`v11`) for any of this to work. See `documentation/observability/prometheus_grafana_jaeger_loki.md`.

---

## Licence

BSD-3-Clause (same as the rest of EcoSystem).
