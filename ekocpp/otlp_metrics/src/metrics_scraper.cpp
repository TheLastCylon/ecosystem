#include "metrics_scraper.hpp"

#include <chrono>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>

#include <asio/steady_timer.hpp>
#include <asio/use_awaitable.hpp>
#include <nlohmann/json.hpp>

#include "clients/transient_tcp_client.hpp"
#include "clients/transient_uds_client.hpp"
#include "clients/udp_client.hpp"
#include "data_transfer_objects/span_key.hpp"
#include "logs/eco_logger.hpp"
#include "stats_translator.hpp"

namespace {

std::shared_ptr<ClientBase> make_client(
    const asio::any_io_executor& executor,
    const DiscoveredService&     service)
{
    if (service.protocol == "udp") {
        return std::make_shared<UDPClient>(executor, *service.host, *service.port);
    }
    if (service.protocol == "tcp") {
        return std::make_shared<TransientTCPClient>(executor, *service.host, *service.port);
    }
    if (service.protocol == "uds") {
        return std::make_shared<TransientUDSClient>(executor, *service.path);
    }
    return nullptr;
}

long long now_unix_nano() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::system_clock::now().time_since_epoch()
    ).count();
}

} // namespace

MetricsScraper::MetricsScraper(
    asio::any_io_executor            executor,
    std::vector<DiscoveredService>   services,
    std::shared_ptr<OtlpMetricsExporter> exporter,
    std::chrono::seconds             poll_interval)
    : executor_(executor)
    , exporter_(std::move(exporter))
    , poll_interval_(poll_interval)
{
    for (auto& svc : services) {
        auto client = make_client(executor_, svc);
        if (!client) {
            spdlog::warn("MetricsScraper: unknown protocol '{}' for service '{}-{}' -- skipping",
                         svc.protocol, svc.name, svc.instance);
            continue;
        }
        targets_.push_back({std::move(svc), std::move(client)});
    }
    spdlog::info("MetricsScraper started. Monitoring {} service(s). Poll interval: {}s",
                 targets_.size(), poll_interval_.count());
}

asio::awaitable<void> MetricsScraper::run() {
    for (;;) {
        asio::steady_timer timer(executor_, poll_interval_);
        co_await timer.async_wait(asio::use_awaitable);

        for (const ScrapeTarget& target : targets_) {
            const auto& svc = target.service;
            const std::map<std::string, std::string> base_labels{{"service", svc.name}, {"instance", svc.instance}};
            try {
                const nlohmann::json request{{"type", "gathered"}};
                const nlohmann::json response = co_await target.client->send_message("eco.statistics.get", request, SpanKey::generate());

                if (!response.contains("statistics")) {
                    spdlog::warn("MetricsScraper: no 'statistics' key in response from '{}-{}'", svc.name, svc.instance);
                    exporter_->push(svc.name, svc.instance, {{"ekosis_service_health", 0.0, base_labels}}, now_unix_nano());
                    continue;
                }

                auto metrics = translate_gathered_stats(response["statistics"], svc.name, svc.instance);
                metrics.push_back({"ekosis_service_health", 1.0, base_labels});
                exporter_->push(svc.name, svc.instance, metrics, now_unix_nano());

            } catch (const std::exception& e) {
                spdlog::warn("MetricsScraper: failed to scrape '{}-{}': {}", svc.name, svc.instance, e.what());
                exporter_->push(svc.name, svc.instance, {{"ekosis_service_health", 0.0, base_labels}}, now_unix_nano());
            }
        }
    }
}
