#include "service_discovery.hpp"

#include <algorithm>
#include <cstdlib>
#include <netdb.h>
#include <string>
#include <unistd.h>
#include <unordered_set>
#include <vector>

extern char** environ;

namespace {

std::unordered_set<std::string> local_addresses() {
    std::unordered_set<std::string> addrs{"127.0.0.1", "localhost", "0.0.0.0"};
    char hostname[256];
    if (::gethostname(hostname, sizeof(hostname)) == 0) {
        addrs.insert(hostname);
        struct hostent* he = ::gethostbyname(hostname);
        if (he) {
            for (char** addr = he->h_addr_list; *addr; ++addr) {
                // h_addr_list entries are in_addr in network byte order --
                // convert to dotted-decimal for string comparison.
                unsigned char* b = reinterpret_cast<unsigned char*>(*addr);
                addrs.insert(
                    std::to_string(b[0]) + "." + std::to_string(b[1]) + "." +
                    std::to_string(b[2]) + "." + std::to_string(b[3])
                );
            }
        }
    }
    return addrs;
}

// "ROUTER_0" -> ("router", "0")
// "MAGIC_EIGHT_BALL_0" -> ("magic_eight_ball", "0")
std::pair<std::string, std::string> parse_name_instance(const std::string& raw) {
    const auto pos = raw.rfind('_');
    if (pos == std::string::npos || pos == 0) {
        return {raw, "0"};
    }
    std::string name = raw.substr(0, pos);
    std::transform(name.begin(), name.end(), name.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return {name, raw.substr(pos + 1)};
}

} // namespace

std::vector<DiscoveredService> discover_local_services() {
    const std::unordered_set<std::string> locals = local_addresses();
    std::vector<DiscoveredService> services;
    constexpr std::string_view PREFIX = "ECOENV_";

    for (char** env = environ; *env; ++env) {
        const std::string entry(*env);
        const auto eq_pos = entry.find('=');
        if (eq_pos == std::string::npos) continue;

        const std::string key   = entry.substr(0, eq_pos);
        const std::string value = entry.substr(eq_pos + 1);

        if (key.rfind(PREFIX, 0) != 0) continue;
        const std::string remainder = key.substr(PREFIX.size());

        for (const std::string_view proto : {"TCP_", "UDP_", "UDS_"}) {
            if (remainder.rfind(proto, 0) != 0) continue;

            const std::string raw_name = remainder.substr(proto.size());
            auto [name, instance] = parse_name_instance(raw_name);

            if (proto == "UDS_") {
                services.push_back({name, instance, "uds", std::nullopt, std::nullopt, value});
                break;
            }

            const auto colon = value.rfind(':');
            if (colon == std::string::npos) break;

            const std::string host     = value.substr(0, colon);
            const std::string port_str = value.substr(colon + 1);
            if (locals.find(host) == locals.end()) break;

            int port = 0;
            try { port = std::stoi(port_str); } catch (...) { break; }

            const std::string protocol = proto == "TCP_" ? "tcp" : "udp";
            services.push_back({name, instance, protocol, host, port, std::nullopt});
            break;
        }
    }

    return services;
}
