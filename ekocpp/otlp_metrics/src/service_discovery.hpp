#pragma once

#include <optional>
#include <string>
#include <vector>

struct DiscoveredService {
    std::string           name;
    std::string           instance;
    std::string           protocol; // "tcp", "udp", "uds"
    std::optional<std::string> host;
    std::optional<int>         port;
    std::optional<std::string> path;
};

// Mirrors ekosis_prometheus/service_discovery.py's discover_local_services().
// Scans environment variables with ECOENV_TCP_*, ECOENV_UDP_*, ECOENV_UDS_*
// prefixes and returns a DiscoveredService for each well-formed entry.
// TCP/UDP entries are filtered to local addresses only (same as Python).
std::vector<DiscoveredService> discover_local_services();
