#include <algorithm>
#include <cctype>
#include <chrono>
#include <memory>
#include <string>
#include <vector>

#include <asio/awaitable.hpp>

#include "application_base.hpp"
// #include "clients/udp_client.hpp"
// #include "clients/transient_tcp_client.hpp"
// #include "clients/persisted_tcp_client.hpp"
// #include "clients/transient_uds_client.hpp"
#include "clients/persisted_uds_client.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "initiate_otlp_tracing.hpp"
// #include "logs/eco_logger.hpp"
#include "sending/buffered_sender.hpp"

#include "fortunes_dto.hpp"
#include "joker_dto.hpp"
#include "lottery_dto.hpp"
#include "magic_eight_ball_dto.hpp"
#include "router_dto.hpp"
#include "time_reporter_dto.hpp"
// #include "tracker_dto.hpp"

namespace {

double unix_now() {
    return std::chrono::duration<double>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}

std::string to_lower(const std::string& s) {
    std::string r = s;
    for (auto& c : r) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return r;
}

std::string list_to_string(const std::vector<std::string>& v) {
    std::string result;
    for (const auto& s : v) result += s + "\n";
    return result;
}

} // namespace

class RouterServer : public ApplicationBase {
public:
    RouterServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        auto exec = io_context().get_executor();

        // fortunes_client_      = std::make_shared<TransientUDSClient>(exec, "127.0.0.1", 8100);
        // joker_client_         = std::make_shared<TransientUDSClient>(exec, "127.0.0.1", 8200);
        // lottery_client_       = std::make_shared<TransientUDSClient>(exec, "127.0.0.1", 8300);
        // magic8ball_client_    = std::make_shared<TransientUDSClient>(exec, "127.0.0.1", 8400);
        // time_reporter_client_ = std::make_shared<TransientUDSClient>(exec, "127.0.0.1", 8500);
        // tracker_client_       = std::make_shared<TransientUDSClient>(exec, "127.0.0.1", 8700);

        fortunes_client_      = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/fortunes_0.uds.sock");
        joker_client_         = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/joker_0.uds.sock");
        lottery_client_       = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/lottery_0.uds.sock");
        magic8ball_client_    = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/magic_eight_ball_0.uds.sock");
        time_reporter_client_ = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/time_reporter_0.uds.sock");
        tracker_client_       = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/tracker_0.uds.sock");

        log_request_sender_  = register_buffered_sender("app.log_request",  tracker_client_, std::chrono::milliseconds{0}, 1000, 10);
        log_response_sender_ = register_buffered_sender("app.log_response", tracker_client_, std::chrono::milliseconds{0}, 1000, 10);

        initiate_otlp_tracing();
        register_endpoint("app.process_message", this, &RouterServer::process_message);
    }

private:
    asio::awaitable<RouterResponseDto> process_message(SpanKey span_key, RouterRequestDto dto) {
        // log_request_sender_->enqueue(TrackerLogRequestDto{dto.request, unix_now()}, span_key);

        const std::string lower   = to_lower(dto.request);
        const std::string keyword = lower.substr(0, lower.find(' '));
        std::string       response;

        if (keyword == "fortune") {
            const auto r = co_await fortunes_client_->send_message<FortuneResponseDto>("app.get_fortune", span_key);
            response = r.fortune;

        } else if (keyword == "joke") {
            const auto r = co_await joker_client_->send_message<JokerResponseDto>("app.get_joke", span_key);
            response = r.joke;

        } else if (keyword == "lotto") {
            int  how_many  = 1;
            auto space_pos = dto.request.find(' ');
            if (space_pos != std::string::npos) {
                try { how_many = std::stoi(dto.request.substr(space_pos + 1)); } catch (...) {}
            }
            const auto r = co_await lottery_client_->send_message<NumberPickerRequestDto, NumberPickerResponseDto>(
                "app.pick_numbers", NumberPickerRequestDto{how_many}, span_key
            );
            response = list_to_string(r.numbers);

        } else if (keyword == "time") {
            const auto r = co_await time_reporter_client_->send_message<CurrentTimeResponseDto>("app.get_time", span_key);
            response = r.time;

        } else {
            const auto r = co_await magic8ball_client_->send_message<Magic8BallResponseDto>("app.get_prediction", span_key);
            response = r.prediction;
        }

        // log_response_sender_->enqueue(TrackerLogRequestDto{response, unix_now()}, span_key);
        co_return RouterResponseDto{response};
    }

    std::shared_ptr<PersistedUDSClient>      fortunes_client_;
    std::shared_ptr<PersistedUDSClient>      joker_client_;
    std::shared_ptr<PersistedUDSClient>      lottery_client_;
    std::shared_ptr<PersistedUDSClient>      magic8ball_client_;
    std::shared_ptr<PersistedUDSClient>      time_reporter_client_;
    std::shared_ptr<PersistedUDSClient>      tracker_client_;
    std::shared_ptr<BufferedSender> log_request_sender_;
    std::shared_ptr<BufferedSender> log_response_sender_;
};

int main(int argc, char** argv) {
    RouterServer app(argc, argv);
    app.start();
}
