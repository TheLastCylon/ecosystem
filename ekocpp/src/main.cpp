#include <spdlog/spdlog.h>

#include "application_base.hpp"
#include "configuration/argument_parser.hpp"
#include "configuration/config_models.hpp"
#include "exceptions/exceptions.hpp"
#include "logs/eco_logger.hpp"

namespace {

// A handler declaring both injectable types, in order -- the simplest
// possible proof that function_traits-based dispatch is wired end to end.
// Returns the received body straight back, so the round trip is visible.
// Logs via spdlog::info rather than std::cout now that EcoLogger/
// OtlpFormatter exist -- proves ambient span_key propagation against real
// traffic, not just the standalone smoke tests.
RequestDTO echo_handler(SpanKey span_key, RequestDTO& dto) {
    spdlog::info("[{}] {}", span_key.to_string(), dto.data.dump());
    return dto;
}

// Registers the echo endpoint in the constructor, per ApplicationBase's
// explicit-registration convention -- this is the first real consumer of
// ApplicationBase itself (lock-file check, configured transports, signal
// shutdown), replacing the hand-rolled io_context/TCPServer that predated it.
class EkocppServer : public ApplicationBase {
public:
    EkocppServer() {
        register_endpoint("echo", echo_handler);
    }
};

} // namespace

int main(int argc, char** argv) {
    const CommandLineArgs args = parse_command_line_args(argc, argv);
    AppConfiguration::initialize(argv[0], args);
    EcoLogger::instance().setup();

    try {
        EkocppServer server;
        server.start();
    } catch (const std::exception& ex) {
        spdlog::error("Fatal: {}", ex.what());
        return 1;
    }

    return 0;
}
