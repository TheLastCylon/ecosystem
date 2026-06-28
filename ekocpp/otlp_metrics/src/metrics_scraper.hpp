#pragma once

#include <chrono>
#include <memory>
#include <string>
#include <vector>

#include <asio/awaitable.hpp>

#include "clients/client_base.hpp"
#include "otlp_metrics_exporter.hpp"
#include "service_discovery.hpp"

// Mirrors ekosis_prometheus/scraper.py's EkosisPrometheusScraper.
// Runs a periodic coroutine that queries eco.statistics.get on each
// discovered service, translates the stats, and pushes to the exporter.
class MetricsScraper {
public:
    MetricsScraper(
        asio::any_io_executor            executor,
        std::vector<DiscoveredService>   services,
        std::shared_ptr<OtlpMetricsExporter> exporter,
        std::chrono::seconds             poll_interval
    );

    asio::awaitable<void> run();

private:
    struct ScrapeTarget {
        DiscoveredService             service;
        std::shared_ptr<ClientBase>   client;
    };

    asio::any_io_executor                executor_;
    std::vector<ScrapeTarget>            targets_;
    std::shared_ptr<OtlpMetricsExporter> exporter_;
    std::chrono::seconds                 poll_interval_;
};
