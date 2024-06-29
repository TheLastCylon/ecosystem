import json
import os


from .config_models import (
    ConfigApplication,
    ConfigApplicationInstance,
    ConfigLogging,
    ConfigStatisticsKeeper,
    ConfigTCP,
    ConfigUDP,
    ConfigUDS,
)


# --------------------------------------------------------------------------------
def env_get_tcp_or_udp(prefix: str, tcp: bool = True) -> ConfigTCP | ConfigUDP | None:
    # expects configuration the form of a string delimited with ':'
    # i.e. "HOST:PORT"
    if tcp:
        env_str = os.environ.get(f"{prefix}_TCP")
    else:
        env_str = os.environ.get(f"{prefix}_UDP")

    if not env_str:
        return None

    host, port  = env_str.split(":")
    if not host:
        return None

    if not port or not int(port):
        return None

    if tcp:
        return ConfigTCP(host=host, port=int(port))
    else:
        return ConfigUDP(host=host, port=int(port))


# --------------------------------------------------------------------------------
def env_get_tcp(prefix: str) -> ConfigUDP | None:
    return env_get_tcp_or_udp(prefix, tcp=True)


# --------------------------------------------------------------------------------
def env_get_udp(prefix: str) -> ConfigUDP | None:
    return env_get_tcp_or_udp(prefix, tcp=False)


# --------------------------------------------------------------------------------
def env_get_uds(prefix: str) -> ConfigUDS | None:
    # Expect an absolute path.
    env_str = os.environ.get(f"{prefix}_UDS")

    if not env_str:
        return None

    directory        = os.path.dirname(env_str)
    socket_file_name = os.path.basename(env_str)

    if not directory or not socket_file_name:
        return None

    if not os.path.isdir(directory):
        return None

    return ConfigUDS(directory=directory, socket_file_name=socket_file_name)


# --------------------------------------------------------------------------------
def env_get_stats(prefix: str) -> ConfigStatisticsKeeper:
    stats_keeper_config = ConfigStatisticsKeeper(gather_period = 300, history_length = 12)

    env_gp_str = os.environ.get(f"{prefix}_STATS_GP")
    if env_gp_str and int(env_gp_str):
        stats_keeper_config.gather_period = int(env_gp_str)

    env_hl_str = os.environ.get(f"{prefix}_STATS_HL")
    if env_hl_str and int(env_hl_str):
        stats_keeper_config.history_length = int(env_hl_str)

    return stats_keeper_config


# --------------------------------------------------------------------------------
def env_get_logging(prefix: str) -> ConfigLogging:
    logging_config = ConfigLogging()

    env_log_dir_str = os.environ.get(f"{prefix}_LOG_DIR")
    env_log_msz_str = os.environ.get(f"{prefix}_LOG_MSZ")
    env_log_mxf_str = os.environ.get(f"{prefix}_LOG_MXF")

    if env_log_dir_str and os.path.isdir(env_log_dir_str):
        logging_config.file_logging.directory = env_log_dir_str

    if env_log_msz_str and int(env_log_msz_str):
        logging_config.file_logging.max_size_in_bytes = int(env_log_msz_str)

    if env_log_mxf_str and int(env_log_mxf_str):
        logging_config.file_logging.max_files = int(env_log_mxf_str)

    return logging_config


# --------------------------------------------------------------------------------
def load_config_from_environment(app_name: str, app_instance: str) -> ConfigApplication:
    env_name                    = app_name.upper()
    env_instance                = app_instance.upper()
    environment_variable_prefix = f"ECO_ENV_{env_name}_{env_instance}"
    app_instance_config         = ConfigApplicationInstance(
        instance_id = app_instance
    )

    tcp_config                  = env_get_tcp(environment_variable_prefix)
    udp_config                  = env_get_udp(environment_variable_prefix)
    uds_config                  = env_get_uds(environment_variable_prefix)
    stats_keeper_config         = env_get_stats(environment_variable_prefix)
    logging_config              = env_get_logging(environment_variable_prefix)

    if tcp_config:
        app_instance_config.tcp = tcp_config

    if udp_config:
        app_instance_config.udp = udp_config

    if uds_config:
        app_instance_config.uds = uds_config

    app_instance_config.stats_keeper   = stats_keeper_config
    app_instance_config.logging        = logging_config
    app_config                         = ConfigApplication(name = app_name, running_instance = app_instance)
    app_config.instances[app_instance] = app_instance_config
    return app_config


# --------------------------------------------------------------------------------
def load_config_from_file(file_path: str) -> ConfigApplication:
    with open(file_path, 'r') as f:
        config_json = json.load(f)
        return ConfigApplication(**config_json)

# config = load_config_from_environment("base", "0")
# config = load_config_from_file('/tmp/base_config.json')
# print(config.json())
