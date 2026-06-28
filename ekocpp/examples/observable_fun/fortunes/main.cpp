#include <fstream>
#include <random>
#include <string>
#include <vector>
#include <spdlog/spdlog.h>

#include "application_base.hpp"
#include "configuration/config_models.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "fortunes_dto.hpp"
#include "initiate_otlp_tracing.hpp"

class FortuneServer : public ApplicationBase {
public:
    FortuneServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        const std::string path = AppConfiguration::instance().extra("FORTUNES_DATA_FILE");
        load_data(path);
        initiate_otlp_tracing();
        register_endpoint("app.get_fortune", this, &FortuneServer::get_fortune);
    }

private:
    FortuneResponseDto get_fortune(SpanKey span_key)
    {
        spdlog::info("RCV: [{}]", span_key.to_string());
        return {lines_[dist_(rng_)]};
    }

    void load_data(const std::string& path)
    {
        spdlog::info("Loading data from path: [{}]", path);

        std::ifstream file(path);
        if (!file.is_open()) {
            throw std::runtime_error("Data file not found or could not be opened: [{}]" + path);
        }

        std::string line;
        while (std::getline(file, line)) {
            if (!line.empty()) lines_.push_back(line);
        }

        if (lines_.empty()) {
            throw std::runtime_error("Data file is empty: [{}]" + path);
        }

        dist_ = std::uniform_int_distribution<size_t>(0, lines_.size() - 1);
        spdlog::info("Data line count: [{}]", lines_.size());
    }

    std::vector<std::string>               lines_;
    std::mt19937                           rng_{std::random_device{}()};
    std::uniform_int_distribution<size_t>  dist_{0, 0};
};

int main(int argc, char** argv) {
    FortuneServer app(argc, argv);
    app.start();
}
