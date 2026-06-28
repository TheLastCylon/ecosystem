#include <chrono>
#include <memory>

#include <asio/co_spawn.hpp>
#include <asio/detached.hpp>

#include <spdlog/spdlog.h>

#include "application_base.hpp"
#include "configuration/config_models.hpp"

#include "metrics_scraper.hpp"
#include "otlp_metrics_exporter.hpp"
#include "service_discovery.hpp"

class MetricsApp : public ApplicationBase {
public:
    MetricsApp(int argc, char** argv) : ApplicationBase(argc, argv) {
        const AppConfiguration& config = AppConfiguration::instance();

        const std::string endpoint = config.extra("OTLP_METRICS_ENDPOINT",
            "http://localhost:9090/api/v1/otlp/v1/metrics");

        const std::string scope_name = config.name() + "-" + config.instance_id();

        const std::chrono::seconds poll_interval{config.stats_keeper().gather_period};

        auto services = discover_local_services();
        if (services.empty()) {
            spdlog::warn("MetricsApp: no services discovered via ECOENV_TCP_*/UDP_*/UDS_* -- nothing to scrape");
        }

        exporter_ = std::make_shared<OtlpMetricsExporter>(endpoint, scope_name);
        scraper_  = std::make_unique<MetricsScraper>(
            io_context().get_executor(),
            std::move(services),
            exporter_,
            poll_interval
        );

        spdlog::info("MetricsApp: OTLP endpoint: {}", endpoint);
    }

protected:
    void setup_tasks() override {
        asio::co_spawn(io_context().get_executor(), scraper_->run(), asio::detached);
    }

private:
    std::shared_ptr<OtlpMetricsExporter> exporter_;
    std::unique_ptr<MetricsScraper>      scraper_;
};

int main(int argc, char** argv) {
    try {
        MetricsApp app(argc, argv);
        app.start();
    } catch (const std::exception& ex) {
        spdlog::error("Fatal: {}", ex.what());
        return 1;
    }
    return 0;
}
