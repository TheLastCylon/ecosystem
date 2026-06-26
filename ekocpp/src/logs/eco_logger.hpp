#pragma once

#include <memory>
#include <string>

#include <spdlog/spdlog.h>

// Mirrors ekosis/logs/logger.py's EcoLogger. Sets up the root spdlog logger
// from AppConfiguration::instance().logging() -- console sink, file sink
// (EkosisRotatingFileSink, see ekosis_rotating_file_sink.hpp), or both,
// matching console_only/file_only exactly. Formatting (OtlpLogRecord/
// OtlpFormatter equivalent) is NOT yet wired in -- this is the rotation/
// sink-selection piece; the JSON log shape is the next session's work, see
// documentation/logging.md.
//
// Singleton via a plain function-local static (Meyers singleton) -- unlike
// AppConfiguration, this has no construction-time external input of its
// own (everything it needs comes from AppConfiguration::instance(), already
// initialized by the time setup() is called from main()), so there's no
// need for AppConfiguration's two-phase initialize()/instance() split.
class EcoLogger {
public:
    static EcoLogger& instance();

    // Builds the root logger's sinks from AppConfiguration::instance().logging().
    // Call once, from main(), after AppConfiguration::initialize().
    void setup();

    // Mirrors ekosis/logs/logger.py's EcoLogger.set_level -- "debug"/"info"/
    // "warn"/"error"/"critical", anything else falls through to info, same
    // permissiveness as Python's chain of plain `if`s. Used by eco.log.level.
    void set_level(const std::string& level);

private:
    EcoLogger() = default;

    std::shared_ptr<spdlog::logger> logger_;
};
