#include <spdlog/spdlog.h>

#include "application_base.hpp"
#include "exceptions/exceptions.hpp"

namespace {

RequestDTO echo_handler(SpanKey span_key, RequestDTO& dto) {
    spdlog::info("[{}] {}", span_key.to_string(), dto.data.dump());
    return dto;
}

class EkocppServer : public ApplicationBase {
public:
    EkocppServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        register_endpoint("echo", echo_handler);
    }
};

} // namespace

int main(int argc, char** argv) {
    try {
        EkocppServer server(argc, argv);
        server.start();
    } catch (const std::exception& ex) {
        spdlog::error("Fatal: {}", ex.what());
        return 1;
    }

    return 0;
}
