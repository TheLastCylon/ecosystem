#include <chrono>
#include <ctime>
#include <string>

#include "application_base.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "initiate_otlp_tracing.hpp"
#include "time_reporter_dto.hpp"

namespace {

const char* week_days[] = {
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
};

std::string current_time_string() {
    const auto   now    = std::chrono::system_clock::now();
    const auto   time_t = std::chrono::system_clock::to_time_t(now);
    const std::tm tm    = *std::localtime(&time_t);
    char          buf[32];
    std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S.000000", &tm);
    return std::string(week_days[tm.tm_wday]) + " " + buf;
}

} // namespace

class TimeReporterServer : public ApplicationBase {
public:
    TimeReporterServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        initiate_otlp_tracing();
        register_endpoint("app.get_time", this, &TimeReporterServer::get_time);
    }

private:
    CurrentTimeResponseDto get_time(SpanKey span_key)
    {
        spdlog::info("RCV: [{}]", span_key.to_string());
        return {current_time_string()};
    }
};

int main(int argc, char** argv) {
    TimeReporterServer app(argc, argv);
    app.start();
}
