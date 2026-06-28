#include <algorithm>
#include <iomanip>
#include <numeric>
#include <random>
#include <sstream>
#include <string>
#include <vector>

#include "application_base.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "initiate_otlp_tracing.hpp"
#include "lottery_dto.hpp"

namespace {

std::string pick_number_set(std::mt19937& rng) {
    std::vector<int> pool(51);
    std::iota(pool.begin(), pool.end(), 1); // 1..51
    std::shuffle(pool.begin(), pool.end(), rng);
    // First 6 = selection (sorted), 7th = bonus ball -- mirrors Python's pick_number_set
    std::vector<int> selection(pool.begin(), pool.begin() + 6);
    std::sort(selection.begin(), selection.end());
    const int bonus = pool[6];
    std::ostringstream oss;
    for (int i = 0; i < 6; ++i) {
        if (i > 0) oss << ", ";
        oss << std::setw(2) << selection[i];
    }
    oss << " [" << std::setw(2) << bonus << "]";
    return oss.str();
}

} // namespace

class LotteryServer : public ApplicationBase {
public:
    LotteryServer(int argc, char** argv) : ApplicationBase(argc, argv) {
        initiate_otlp_tracing();
        register_endpoint("app.pick_numbers", this, &LotteryServer::pick_numbers);
    }

private:
    NumberPickerResponseDto pick_numbers(SpanKey span_key, NumberPickerRequestDto dto) {
        spdlog::info("RCV: [{}]", span_key.to_string());
        std::vector<std::string> results;
        results.reserve(dto.how_many);
        for (int i = 0; i < dto.how_many; ++i)
            results.push_back(pick_number_set(rng_));
        return {results};
    }

    std::mt19937 rng_{std::random_device{}()};
};

int main(int argc, char** argv) {
    LotteryServer app(argc, argv);
    app.start();
}
