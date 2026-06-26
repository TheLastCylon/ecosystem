#include "config_models.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <fstream>
#include <memory>

#include <nlohmann/json.hpp>

namespace {

std::unique_ptr<AppConfiguration> g_instance;

std::string basename_of(const char* path) {
    const std::string s = path;
    const auto         slash = s.find_last_of('/');
    return slash == std::string::npos ? s : s.substr(slash + 1);
}

std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) { return std::toupper(c); });
    return s;
}

std::optional<std::pair<std::string, uint16_t>> parse_host_port_string(const std::string& value) {
    const auto colon = value.find(':');
    if (colon == std::string::npos) return std::nullopt;
    const std::string host = value.substr(0, colon);
    const std::string port = value.substr(colon + 1);
    if (host.empty() || port.empty()) return std::nullopt;
    return std::make_pair(host, static_cast<uint16_t>(std::stoi(port)));
}

} // namespace

void AppConfiguration::initialize(const char* argv0, const CommandLineArgs& args) {
    g_instance.reset(new AppConfiguration(argv0, args));
}

AppConfiguration& AppConfiguration::instance() {
    return *g_instance; // calling before initialize() is a programmer error, not a recoverable condition
}

AppConfiguration::AppConfiguration(const char* argv0, const CommandLineArgs& args)
    : application_name_(basename_of(argv0)), instance_(args.instance) {
    // console_only/file_only are CLI-only on the Python side too (no env
    // var equivalent) -- read directly off args, not through get_eco_env.
    logging_.console_only = args.log_console_only;
    logging_.file_only    = args.log_file_only;

    load_from_env();
    if (args.config_file) {
        load_from_file(*args.config_file);
    }
}

const std::string& AppConfiguration::name() const { return application_name_; }
const std::string& AppConfiguration::instance_id() const { return instance_; }
const std::string& AppConfiguration::lock_directory() const { return lock_directory_; }
const std::optional<std::string>& AppConfiguration::buffer_directory() const { return buffer_directory_; }

const std::optional<ConfigTCP>& AppConfiguration::tcp() const { return tcp_; }
const std::optional<ConfigUDP>& AppConfiguration::udp() const { return udp_; }
const std::optional<ConfigUDS>& AppConfiguration::uds() const { return uds_; }
const ConfigLogging&            AppConfiguration::logging() const { return logging_; }
const ConfigStatisticsKeeper&   AppConfiguration::stats_keeper() const { return stats_keeper_; }

std::optional<std::string> AppConfiguration::get_eco_env_optional(const std::string& postfix, bool instance_level_only) const {
    const std::string global_env_name    = "ECOENV_" + postfix;
    const std::string app_level_env_name = global_env_name + "_" + to_upper(application_name_);
    const std::string instance_env_name  = app_level_env_name + "_" + to_upper(instance_);

    if (const char* v = std::getenv(instance_env_name.c_str())) return std::string(v);
    if (instance_level_only) return std::nullopt;
    if (const char* v = std::getenv(app_level_env_name.c_str())) return std::string(v);
    if (const char* v = std::getenv(global_env_name.c_str())) return std::string(v);
    return std::nullopt;
}

std::string AppConfiguration::get_eco_env(const std::string& postfix, const std::string& default_value, bool instance_level_only) const {
    return get_eco_env_optional(postfix, instance_level_only).value_or(default_value);
}

void AppConfiguration::load_from_env() {
    lock_directory_   = get_eco_env("LOCK_DIR", "/tmp");
    buffer_directory_ = get_eco_env_optional("BUFFER_DIR"); // deliberately no default -- see the comment on buffer_directory_'s declaration

    stats_keeper_.gather_period  = std::stoi(get_eco_env("STAT_GP", "300"));
    stats_keeper_.history_length = std::stoi(get_eco_env("STAT_HL", "12"));

    if (const auto tcp_string = get_eco_env_optional("TCP", true)) {
        if (const auto host_port = parse_host_port_string(*tcp_string)) {
            tcp_ = ConfigTCP{host_port->first, host_port->second};
        }
    }

    if (const auto udp_string = get_eco_env_optional("UDP", true)) {
        if (const auto host_port = parse_host_port_string(*udp_string)) {
            udp_ = ConfigUDP{host_port->first, host_port->second};
        }
    }

    if (const auto uds_string = get_eco_env_optional("UDS", true)) {
        const auto slash = uds_string->find_last_of('/');
        if (slash != std::string::npos) {
            ConfigUDS config;
            config.directory        = uds_string->substr(0, slash);
            config.socket_file_name = uds_string->substr(slash + 1);
            if (config.socket_file_name == "DEFAULT") {
                config.socket_file_name = application_name_ + "_" + instance_ + ".uds.sock";
            }
            uds_ = config;
        }
    }

    logging_.level                          = get_eco_env("LOG_LEVEL", "info");
    logging_.file_logging.directory         = get_eco_env("LOG_DIR", "/tmp");
    logging_.file_logging.buffer_size       = std::stoi(get_eco_env("LOG_BUF_SIZE", "0"));
    logging_.file_logging.max_size_in_bytes = std::stoull(get_eco_env("LOG_MAX_SIZE", "10485760"));
    logging_.file_logging.max_files         = std::stoi(get_eco_env("LOG_MAX_FILES", "10"));

    // base_file_name/base_file_path are computed, not user-configurable --
    // mirrors Python's EcoLogger.setup(), which builds these from
    // app_config.name/instance rather than taking them as input.
    logging_.file_logging.base_file_name = application_name_ + "-" + instance_;
    logging_.file_logging.base_file_path = logging_.file_logging.directory + "/" + logging_.file_logging.base_file_name + ".log";
}

void AppConfiguration::load_from_file(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("The specified configuration file [" + path + "] does NOT exist or could not be opened.");
    }

    nlohmann::json config_json;
    file >> config_json;

    // Mirrors ekosis's ConfigApplicationInstance shape, flattened -- only
    // the fields ekocpp currently has a consumer for. A config file value,
    // when present, overrides whatever load_from_env() already set.
    if (config_json.contains("lock_directory")) {
        lock_directory_ = config_json.at("lock_directory").get<std::string>();
    }
    if (config_json.contains("buffer_directory") && !config_json.at("buffer_directory").is_null()) {
        buffer_directory_ = config_json.at("buffer_directory").get<std::string>();
    }
    if (config_json.contains("stats_keeper") && !config_json.at("stats_keeper").is_null()) {
        const auto& stats_json       = config_json.at("stats_keeper");
        stats_keeper_.gather_period  = stats_json.value("gather_period", stats_keeper_.gather_period);
        stats_keeper_.history_length = stats_json.value("history_length", stats_keeper_.history_length);
    }
    if (config_json.contains("tcp") && !config_json.at("tcp").is_null()) {
        const auto& tcp_json = config_json.at("tcp");
        tcp_ = ConfigTCP{tcp_json.value("host", std::string{"127.0.0.1"}), tcp_json.value("port", uint16_t{8888})};
    }
    if (config_json.contains("udp") && !config_json.at("udp").is_null()) {
        const auto& udp_json = config_json.at("udp");
        udp_ = ConfigUDP{udp_json.value("host", std::string{"127.0.0.1"}), udp_json.value("port", uint16_t{8889})};
    }
    if (config_json.contains("uds") && !config_json.at("uds").is_null()) {
        const auto& uds_json = config_json.at("uds");
        uds_ = ConfigUDS{
            uds_json.value("directory", std::string{"/tmp"}),
            uds_json.value("socket_file_name", std::string{"DEFAULT"})
        };
    }
    if (config_json.contains("logging") && !config_json.at("logging").is_null()) {
        const auto& logging_json = config_json.at("logging");
        logging_.level = logging_json.value("level", logging_.level);
        if (logging_json.contains("file_logging") && !logging_json.at("file_logging").is_null()) {
            const auto& file_json                   = logging_json.at("file_logging");
            logging_.file_logging.directory         = file_json.value("directory", logging_.file_logging.directory);
            logging_.file_logging.buffer_size       = file_json.value("buffer_size", logging_.file_logging.buffer_size);
            logging_.file_logging.max_size_in_bytes = file_json.value("max_size_in_bytes", logging_.file_logging.max_size_in_bytes);
            logging_.file_logging.max_files         = file_json.value("max_files", logging_.file_logging.max_files);
        }
        // directory may have just changed -- base_file_path must reflect it,
        // same recompute load_from_env() already does after setting directory.
        logging_.file_logging.base_file_path = logging_.file_logging.directory + "/" + logging_.file_logging.base_file_name + ".log";
    }
}
