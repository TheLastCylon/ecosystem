#include "eco_logger.hpp"

#include <chrono>
#include <vector>

#include <spdlog/sinks/stdout_color_sinks.h>

#include "ekosis_rotating_file_sink.hpp"
#include "otlp_formatter.hpp"
#include "../configuration/config_models.hpp"

namespace {

// Mirrors ekosis/logs/logger.py's EcoLogger.set_level -- string level name
// to spdlog's level_enum. Unrecognised values fall through to info, same
// permissiveness as Python's chain of plain `if` statements (no else/raise
// on an unmatched string there either).
spdlog::level::level_enum level_from_string(const std::string& level) {
    if (level == "debug")    return spdlog::level::debug;
    if (level == "info")     return spdlog::level::info;
    if (level == "warn")     return spdlog::level::warn;
    if (level == "error")    return spdlog::level::err;
    if (level == "critical") return spdlog::level::critical;
    return spdlog::level::info;
}

} // namespace

EcoLogger& EcoLogger::instance() {
    static EcoLogger logger;
    return logger;
}

void EcoLogger::setup() {
    const ConfigLogging& log_config = AppConfiguration::instance().logging();
    const auto            level      = level_from_string(log_config.level);

    std::vector<spdlog::sink_ptr> sinks;

    if (!log_config.console_only) {
        const auto& file_config = log_config.file_logging;
        sinks.push_back(std::make_shared<EkosisRotatingFileSinkMt>(
            file_config.base_file_path, file_config.max_size_in_bytes, file_config.max_files));
    }

    if (!log_config.file_only) {
        sinks.push_back(std::make_shared<spdlog::sinks::stdout_color_sink_mt>());
    }

    logger_ = std::make_shared<spdlog::logger>("ekocpp", sinks.begin(), sinks.end());
    logger_->set_level(level);
    logger_->flush_on(spdlog::level::warn);
    logger_->set_formatter(std::make_unique<OtlpFormatter>());

    spdlog::set_default_logger(logger_);

    // Console sinks fflush() on every write (confirmed in spdlog's own
    // ansicolor_sink-inl.h); file sinks don't -- only flush_on()'s level
    // threshold or an explicit flush() call moves their buffered bytes to
    // disk. ekocpp has no graceful-shutdown signal handling of its own yet
    // (ApplicationBase has it, this minimal main.cpp doesn't use
    // ApplicationBase) -- without this, an abrupt kill loses whatever's
    // still sitting in the file sink's buffer below INFO/WARN. A periodic
    // flush bounds that loss to ~1s of logs regardless of how the process
    // actually exits.
    spdlog::flush_every(std::chrono::seconds(1));
}

void EcoLogger::set_level(const std::string& level) {
    logger_->set_level(level_from_string(level));
}
