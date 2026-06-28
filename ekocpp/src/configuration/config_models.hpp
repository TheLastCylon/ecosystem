#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>

#include "argument_parser.hpp"

// Mirrors ekosis/configuration/config_models.py's ConfigTCP/ConfigUDP/ConfigUDS.
struct ConfigTCP {
    std::string host = "127.0.0.1";
    uint16_t    port = 8888;
};

struct ConfigUDP {
    std::string host = "127.0.0.1";
    uint16_t    port = 8889;
};

struct ConfigUDS {
    std::string directory        = "/tmp"; // socket files shouldn't survive a reboot
    std::string socket_file_name = "DEFAULT";
};

// Mirrors ekosis/configuration/config_models.py's ConfigLoggingFile.
// base_file_name/base_file_path are computed once AppConfiguration knows
// the app name/instance (see config_models.cpp), not user-configurable --
// same reasoning as Python's setup(), which builds these from
// app_config.name/instance rather than taking them as input.
struct ConfigLoggingFile {
    std::string directory         = "/tmp"; // ECOENV_LOG_DIR, platform_default_dir on the Python side
    std::string base_file_name;
    std::string base_file_path;
    int         buffer_size       = 0;        // ECOENV_LOG_BUF_SIZE, 0 = unbuffered
    size_t      max_size_in_bytes = 10485760; // ECOENV_LOG_MAX_SIZE, 10MB
    int         max_files         = 10;       // ECOENV_LOG_MAX_FILES
};

// Mirrors ekosis/configuration/config_models.py's ConfigLogging. Unlike
// ConfigTCP/ConfigUDP/ConfigUDS, NOT optional on AppConfiguration -- logging
// always has a real config, on by default for both console and file (same
// "force a conscious choice" reasoning as the Python side: console_only/
// file_only default false, so backgrounding the process never silently
// loses all logging).
struct ConfigLogging {
    bool              console_only = false; // -lco / --log_console_only
    bool              file_only    = false; // -lfo / --log_file_only
    ConfigLoggingFile file_logging;
    std::string       level        = "info"; // ECOENV_LOG_LEVEL
};

// Mirrors ekosis/configuration/config_models.py's ConfigStatisticsKeeper.
struct ConfigStatisticsKeeper {
    int gather_period  = 300; // ECOENV_STAT_GP, 5 minutes
    int history_length = 12;  // ECOENV_STAT_HL, an hour's worth at the default gather_period
};

// Mirrors ekosis/configuration/config_models.py's AppConfiguration --
// flattened down to what ekocpp actually has a consumer for today (TCP/UDP/
// UDS server config, lock directory, logging, statistics keeper tuning,
// buffer directory). `extra` deliberately not ported -- no consumer for
// it yet. Add it once one exists, same rule already applied to
// ApplicationBase.
//
// buffer_directory is std::optional, not defaulted to /tmp like
// lock_directory -- mirrors Python's deliberate choice (see
// get_app_instance_buffer_directory's own comment) NOT to default this to
// anywhere, since a buffered handler's SQLite queue files silently landing
// in a directory that gets wiped on reboot is a real data-loss risk, worse
// than just failing loudly when it's unset.
//
// Singleton, but not via Python's metaclass trick (no C++ equivalent) and
// not a no-argument Meyers singleton either, since construction genuinely
// needs argv0/CommandLineArgs from main(). Two-phase instead: initialize()
// once, explicitly, from main() -- after that, instance() is the
// no-argument global accessor every other subsystem reaches for. The
// explicit call (not implicit static-init-order magic) is what keeps this
// safe -- same reasoning that ruled out decorator-style endpoint
// registration earlier this project.
class AppConfiguration {
public:
    // argv0 is used to derive the application name (basename, mirroring
    // Python's camel_to_snake(basename(sys.argv[0]).replace(".py", "")) --
    // minus the .py-stripping, which doesn't apply to a compiled binary).
    static void initialize(const char* argv0, const CommandLineArgs& args);
    static AppConfiguration& instance();

    const std::string& name() const;
    const std::string& instance_id() const;
    const std::string& lock_directory() const;
    const std::optional<std::string>& buffer_directory() const;

    const std::optional<ConfigTCP>& tcp() const;
    const std::optional<ConfigUDP>& udp() const;
    const std::optional<ConfigUDS>& uds() const;
    const ConfigLogging&            logging() const;
    const ConfigStatisticsKeeper&   stats_keeper() const;

    // Mirrors ekosis/configuration/config_models.py's get_app_instance_extra() --
    // scans environ at startup and strips the tier-appropriate prefix so that
    // ECOENV_EXTRA_<APP>_<INSTANCE>_<KEY> becomes just <KEY> in the map.
    // Three tiers (global/app/instance); instance wins over app wins over global.
    std::string extra(const std::string& key, const std::string& default_value = "") const;

private:
    AppConfiguration(const char* argv0, const CommandLineArgs& args);

    void load_from_env();
    void load_from_file(const std::string& path);
    void load_extra_from_env();

    // The three-tier ECOENV_<postfix>[_<APP>[_<INSTANCE>]] precedence chain
    // -- instance-level wins, then app-level, then global, then default.
    // instance_level_only mirrors Python's get_instance_env -- skips the
    // app/global fallback tiers entirely for settings that are only ever
    // meaningful per-instance.
    std::string                get_eco_env(const std::string& postfix, const std::string& default_value, bool instance_level_only = false) const;
    std::optional<std::string> get_eco_env_optional(const std::string& postfix, bool instance_level_only = false) const;

    std::string                application_name_;
    std::string                instance_;
    std::string                lock_directory_;
    std::optional<std::string> buffer_directory_;
    std::unordered_map<std::string, std::string> extra_;

    std::optional<ConfigTCP> tcp_;
    std::optional<ConfigUDP> udp_;
    std::optional<ConfigUDS> uds_;
    ConfigLogging            logging_;
    ConfigStatisticsKeeper   stats_keeper_;
};
