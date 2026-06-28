#include <random>
#include <string>
#include <vector>

#include "application_base.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "initiate_otlp_tracing.hpp"
#include "magic_eight_ball_dto.hpp"

static const std::vector<std::string> possible_responses = {
    "It is certain!",
    "It is decidedly so!",
    "Without a doubt!",
    "Yes definitely!",
    "You may rely on it!",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it!",
    R"(My reply is: "No!")",
    R"(My sources say: "No!")",
    "Outlook not so good.",
    "Very doubtful."
};

class Magic8BallServer : public ApplicationBase {
public:
    Magic8BallServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        dist_ = std::uniform_int_distribution<size_t>(0, possible_responses.size() - 1);
        initiate_otlp_tracing();
        register_endpoint("app.get_prediction", this, &Magic8BallServer::get_prediction);
    }

private:
    // Question from request is ignored -- same as Python's get_prediction handler
    Magic8BallResponseDto get_prediction(SpanKey span_key)
    {
        spdlog::info("RCV: [{}]", span_key.to_string());
        return {possible_responses[dist_(rng_)]};
    }

    std::mt19937                           rng_{std::random_device{}()};
    std::uniform_int_distribution<size_t>  dist_{0, 0};
};

int main(int argc, char** argv) {
    Magic8BallServer app(argc, argv);
    app.start();
}
