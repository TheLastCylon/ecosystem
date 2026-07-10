#include <algorithm>
#include <cctype>
#include <chrono>
#include <memory>
#include <string>
#include <vector>

#include <asio/awaitable.hpp>

#include "application_base.hpp"
#include "clients/persisted_uds_client.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "initiate_otlp_tracing.hpp"
#include "sending/buffered_sender.hpp"

#include "fortunes_dto.hpp"
#include "joker_dto.hpp"
#include "lottery_dto.hpp"
#include "magic_eight_ball_dto.hpp"
#include "router_dto.hpp"
#include "time_reporter_dto.hpp"
#include "tracker_dto.hpp"

// --------------------------------------------------------------------------------
namespace {

    // -------------------------------------------------------------------------
    double unix_now() {
        return std::chrono::duration<double>(
            std::chrono::system_clock::now().time_since_epoch()
        ).count();
    }

    // -------------------------------------------------------------------------
    std::string to_lower(const std::string& s) {
        std::string r = s;
        for (auto& c : r) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        return r;
    }

    // -------------------------------------------------------------------------
    std::string list_to_string(const std::vector<std::string>& v) {
        std::string result;
        for (const auto& s : v) result += s + "\n";
        return result;
    }

}

// --------------------------------------------------------------------------------
class RouterServer : public ApplicationBase
{
    public:
        // --------------------------------------------------------------------------------
        RouterServer(int argc, char** argv) : ApplicationBase(argc, argv) {
                auto exec = io_context().get_executor();

                fortunes_client_      = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/fortunes_0.uds.sock");
                joker_client_         = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/joker_0.uds.sock");
                lottery_client_       = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/lottery_0.uds.sock");
                magic8ball_client_    = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/magic_eight_ball_0.uds.sock");
                time_reporter_client_ = std::make_shared<PersistedUDSClient>(exec, "/tmp/observable_fun_cpp/time_reporter_0.uds.sock");

                log_request_sender_   = register_buffered_sender(
                    "app.log_request",
                    std::string{"/tmp/observable_fun_cpp/tracker_0.uds.sock"},
                    std::chrono::milliseconds{0},
                    1000,
                    10
                );

                log_response_sender_  = register_buffered_sender(
                    "app.log_response",
                    std::string{"/tmp/observable_fun_cpp/tracker_0.uds.sock"},
                    std::chrono::milliseconds{0},
                    1000,
                    10
                );

                initiate_otlp_tracing();
                register_endpoint("app.process_message", this, &RouterServer::process_message);
        }

    private:
        // ---------------------------------------------------------------------
        asio::awaitable<std::string> get_fortune() {
            const auto r = co_await fortunes_client_->send_message<FortuneResponseDto>("app.get_fortune");
            co_return r.fortune;
        }

        // ---------------------------------------------------------------------
        asio::awaitable<std::string> get_joke(SpanKey &span_key) {
            const auto r = co_await joker_client_->send_message<JokerResponseDto>("app.get_joke", span_key);
            co_return r.joke;
        }

        // ---------------------------------------------------------------------
        asio::awaitable<std::string> get_lottery(SpanKey &span_key, RouterRequestDto &dto) {
            int  how_many  = 1;
            auto space_pos = dto.request.find(' ');
            if (space_pos != std::string::npos) {
                try {
                    how_many = std::stoi(dto.request.substr(space_pos + 1));
                } catch (...) {
                }
            }
            const auto r = co_await lottery_client_->send_message<NumberPickerRequestDto, NumberPickerResponseDto>(
                "app.pick_numbers",
                NumberPickerRequestDto{how_many},
                span_key
            );
            co_return list_to_string(r.numbers);
        }

        // ---------------------------------------------------------------------
        asio::awaitable<std::string> get_time(SpanKey &span_key) {
            const auto r = co_await time_reporter_client_->send_message<CurrentTimeResponseDto>(
                "app.get_time",
                span_key
            );
            co_return r.time;
        }

        // ---------------------------------------------------------------------
        asio::awaitable<std::string> get_magic_eight_ball(SpanKey &span_key) {
            const auto r = co_await magic8ball_client_->send_message<Magic8BallResponseDto>(
                "app.get_prediction",
                span_key
            );
            co_return r.prediction;
        }

        // ---------------------------------------------------------------------
        asio::awaitable<RouterResponseDto> process_message(
            SpanKey          span_key,
            RouterRequestDto dto
        ) {
            log_request_sender_->enqueue(TrackerLogRequestDto{dto.request, unix_now()}, span_key);

            const std::string lower   = to_lower(dto.request);
            const std::string keyword = lower.substr(0, lower.find(' '));
            std::string       response;

            if (keyword == "fortune") {
                response = co_await get_fortune();
            } else if (keyword == "joke") {
                response = co_await get_joke(span_key);
            } else if (keyword == "lotto") {
                response = co_await get_lottery(span_key, dto);
            } else if (keyword == "time") {
                response = co_await get_time(span_key);
            } else {
                response = co_await get_magic_eight_ball(span_key);
            }

            log_response_sender_->enqueue(TrackerLogRequestDto{response, unix_now()}, span_key);
            co_return RouterResponseDto{response};
        }

        // ---------------------------------------------------------------------
        std::shared_ptr<PersistedUDSClient> fortunes_client_;
        std::shared_ptr<PersistedUDSClient> joker_client_;
        std::shared_ptr<PersistedUDSClient> lottery_client_;
        std::shared_ptr<PersistedUDSClient> magic8ball_client_;
        std::shared_ptr<PersistedUDSClient> time_reporter_client_;
        std::shared_ptr<BufferedSender>     log_request_sender_;
        std::shared_ptr<BufferedSender>     log_response_sender_;
};

// --------------------------------------------------------------------------------
int main(int argc, char** argv) {
    RouterServer app(argc, argv);
    app.start();
}
