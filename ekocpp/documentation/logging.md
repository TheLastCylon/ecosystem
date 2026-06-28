# Logging -- DONE, verified live (2026-06-23)

**Status:** built and verified against real `ekocpp_server` + real `esnc` traffic.
Rotation, config, sink selection, and `OtlpLogRecord`/`OtlpFormatter` are all in place.
The only thing deliberately not done: `filename`/`lineno`/`funcName` attributes require
switching call sites to spdlog's `SPDLOG_INFO`-style macros (plain `spdlog::info()` never
captures source location) -- not done project-wide, see NEXT.

## What ekosis has, for reference

- `ekosis/data_transfer_objects/otlp_log_record.py` -- `OtlpLogRecord` DTO +
  `severity_for_levelno()` (10/20/30/40/50 -> 5/9/13/17/21).
- `ekosis/logs/otlp_formatter.py` -- reads the ambient span_key, builds an
  `OtlpLogRecord`, returns JSON. Duplicates `application_name`/`application_instance`
  into `attributes` -- the only way a human tailing the raw file directly knows which
  app/instance a line came from.
- `ekosis/logs/logger.py` -- `EcoLogger.setup()`.
- `ekosis/logs/buffered_rotating_file_handler.py` -- wraps stdlib's
  `RotatingFileHandler`.
- `ekosis/configuration/config_models.py`'s `ConfigLogging`/`ConfigLoggingFile`.
- `ekosis_log_shipper` -- tails `OtlpLogRecord`-shaped JSON, ships to an
  OTLP-compatible backend. Doesn't care that lines now also come from C++.

## What got built, C++ side

- **`src/logs/ekosis_rotating_file_sink.hpp`** -- `EkosisRotatingFileSink<Mutex>`.
  Extends spdlog's `base_sink<Mutex>` (spdlog's own documented extension point) rather
  than spdlog's own `rotating_file_sink`, because of one real divergence found by
  reading spdlog's actual source: spdlog inserts the backup index BEFORE the extension
  (`mylog.3.txt`); Python's stdlib appends it AFTER the whole filename (`mylog.log.3`).
  Checked whether spdlog supports a customization hook the way `daily_file_sink`/
  `hourly_file_sink` do (a `FileNameCalc` template policy) -- confirmed
  `rotating_file_sink` itself never got the same treatment, a real inconsistency in
  spdlog's own sinks. Writing our own sink avoids depending on whether spdlog ever
  merges anything upstream, while still depending on spdlog itself as a real library,
  not a fork -- everything except `calc_filename` is copied verbatim (MIT) from
  spdlog's own `rotate_()`/`sink_it_()`. Verified live with a forced tiny `max_size`:
  real rotation, real files on disk, exact Python-matching names.
- **`ConfigLoggingFile`/`ConfigLogging`** (`src/configuration/config_models.hpp/.cpp`)
  -- ported into `AppConfiguration` matching `ConfigTCP`/`ConfigUDP`/`ConfigUDS`'s
  existing env/CLI/JSON-file precedence pattern exactly. `-lco`/`-lfo` mutually
  exclusive CLI flags added to `argument_parser.cpp` -- caught and fixed a real bug
  before it shipped: `getopt_long`'s short-option mechanism can't parse a multi-char
  flag like `-lco` at all (only single chars); switched to `getopt_long_only` with
  `"lco"`/`"lfo"` as their own long-option names.
- **`src/data_transfer_objects/otlp_log_record.hpp`** -- `OtlpLogRecord` (mirrors
  `ResponseDTO`'s header-only `to_json()` pattern) + `severity_for_level()`.
  `spdlog::level::trace -> (1, "TRACE")` is a deliberate extension Python's own mapping
  can never reach (stdlib logging has no trace level) -- OTel's spec defines the band,
  so this is a correct addition, not a divergence to chase parity away from.
- **`src/logs/otlp_formatter.{hpp,cpp}`** -- `OtlpFormatter : spdlog::formatter`. Reads
  `thread_local_span_key()` (the vendored asio patch, see `ambient_span_context.md`)
  instead of Python's `ContextVar` -- same idea, different propagation mechanism.
  Timestamp formatted via `gmtime_r`+`snprintf` (not `<chrono>` formatting), matching
  `ekosis_log_shipper`'s own `otlp_envelope.cpp` precedent and its exact expected
  shape (`2026-06-18T17:27:24.331740+00:00`).
- **`src/logs/eco_logger.{hpp,cpp}`** -- `EcoLogger::setup()` builds console
  (`stdout_color_sink_mt`) and/or file (`EkosisRotatingFileSinkMt`) sinks from
  `ConfigLogging`, matching `console_only`/`file_only` branch-for-branch, wires
  `OtlpFormatter` in via `set_formatter()`.
- **`src/main.cpp`** -- now actually calls `parse_command_line_args`/
  `AppConfiguration::initialize`/`EcoLogger::instance().setup()`; `echo_handler` logs
  via `spdlog::info` instead of `std::cout`.

## A real gap found and fixed during live verification

First live test (real server, real `esnc` request, killed after a `sleep`) showed the
log line on console but an EMPTY file -- not a fluke. Read spdlog's own
`ansicolor_sink-inl.h`: the console sink calls `fflush()` on *every* write,
unconditionally. File sinks (ours included) don't -- they only flush via
`flush_on()`'s level threshold or an explicit call. `ekocpp` has no graceful-shutdown
signal handling of its own yet (`ApplicationBase` has it; this minimal `main.cpp`
doesn't use `ApplicationBase`), so an abrupt kill silently lost whatever was still
buffered below INFO/WARN. Fixed with `spdlog::flush_every(std::chrono::seconds(1))` in
`EcoLogger::setup()` -- bounds the loss to ~1s regardless of how the process exits.
Re-verified live: same kill-mid-flight scenario, file and console now show identical
content.

## Verified live

Real `ekocpp_server` + real `esnc` traffic, not synthetic: console and file both show
the same JSON line, `trace_id`/`span_id` matching the real request's `span_key` exactly.
All four `EcoLogger` sink-selection branches (default/`-lco`/`-lfo`/both-together
rejected) verified separately with real CLI flags, real config, real files on disk.

## NEXT

- `filename`/`lineno`/`funcName` attributes are currently never populated --
  `msg.source.empty()` is always true with plain `spdlog::info()` calls. Populating
  them means switching call sites to `SPDLOG_INFO`/`SPDLOG_LOGGER_CALL`-style macros
  project-wide, a deliberate decision not made yet, not an oversight.
- `main.cpp` still doesn't use `ApplicationBase`'s signal-driven graceful shutdown --
  `flush_every` bounds the loss but doesn't eliminate it. Worth revisiting once
  `main.cpp` (or a real application built on `ApplicationBase`) needs a clean exit
  path for other reasons too.
- Upstreaming the `rotating_file_sink` `FileNameCalc` templatization to spdlog was
  considered and explicitly NOT done -- writing our own sink was judged better
  (doesn't depend on spdlog's maintainers' timeline), but the upstream PR itself
  remains a separate, non-blocking, not-yet-started idea if there's ever appetite.
