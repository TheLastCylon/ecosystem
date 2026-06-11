import os
import socket

from dataclasses import dataclass, field
from typing      import List, Optional


# --------------------------------------------------------------------------------
@dataclass
class DiscoveredService:
    name    : str            # e.g. "router"
    instance: str            # e.g. "0"
    protocol: str            # "tcp", "udp", "uds"
    host    : Optional[str]  # host or IP for tcp/udp; None for uds
    port    : Optional[int]  # port for tcp/udp; None for uds
    path    : Optional[str]  # socket path for uds; None for tcp/udp


# --------------------------------------------------------------------------------
def _local_addresses() -> set:
    addresses = {"127.0.0.1", "localhost", "0.0.0.0"}
    try:
        hostname = socket.gethostname()
        addresses.add(hostname)
        addresses.add(socket.gethostbyname(hostname))
    except OSError:
        pass
    return addresses


# --------------------------------------------------------------------------------
def _parse_name_instance(raw: str) -> tuple[str, str]:
    # e.g. "ROUTER_0"          -> ("router", "0")
    # e.g. "MAGIC_EIGHT_BALL_0" -> ("magic_eight_ball", "0")
    parts    = raw.rsplit("_", 1)
    name     = parts[0].lower()
    instance = parts[1] if len(parts) == 2 else "0"
    return name, instance


# --------------------------------------------------------------------------------
def discover_local_services() -> List[DiscoveredService]:
    local_addresses = _local_addresses()
    services        = []
    prefix          = "ECOENV_"

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        remainder = key[len(prefix):]

        for protocol in ("TCP", "UDP", "UDS"):
            proto_prefix = f"{protocol}_"
            if not remainder.startswith(proto_prefix):
                continue

            raw_name = remainder[len(proto_prefix):]
            name, instance = _parse_name_instance(raw_name)

            if protocol == "UDS":
                services.append(DiscoveredService(
                    name     = name,
                    instance = instance,
                    protocol = "uds",
                    host     = None,
                    port     = None,
                    path     = value,
                ))
                break

            # TCP / UDP -- value is "host:port"
            if ":" not in value:
                break
            host, port_str = value.rsplit(":", 1)
            if host not in local_addresses:
                break
            try:
                port = int(port_str)
            except ValueError:
                break

            services.append(DiscoveredService(
                name     = name,
                instance = instance,
                protocol = protocol.lower(),
                host     = host,
                port     = port,
                path     = None,
            ))
            break

    return services
