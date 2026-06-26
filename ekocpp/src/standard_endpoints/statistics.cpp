#include "statistics.hpp"

#include "../state_keepers/statistics_keeper.hpp"

namespace {

RequestDTO eco_statistics_get(SpanKey, RequestDTO& dto) {
    auto&             keeper = StatisticsKeeper::instance();
    const std::string type   = dto.data.value("type", std::string{"last"});

    if (type == "current") {
        return RequestDTO{{{"statistics", keeper.get_current_statistics()}}};
    }
    if (type == "full") {
        return RequestDTO{{{"statistics", keeper.get_full_gathered_statistics()}}};
    }
    return RequestDTO{{{"statistics", keeper.get_last_gathered_statistics()}}};
}

} // namespace

void register_statistics_endpoints(RequestRouter& router) {
    router.register_endpoint("eco.statistics.get", eco_statistics_get);
}
