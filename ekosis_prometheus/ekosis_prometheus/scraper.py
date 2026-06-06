import asyncio
import logging

from typing                             import Dict, List, Optional
from prometheus_client                  import CollectorRegistry, Gauge, push_to_gateway
from ekosis.clients                     import UDPClient, TransientTCPClient, TransientUDSClient
from ekosis.clients.client_base         import ClientBase
from ekosis.sending.sender_base         import SenderBase
from ekosis.data_transfer_objects       import StatsRequestDto, StatsResponseDto
from ekosis.configuration.config_models import AppConfiguration

from .service_discovery                 import DiscoveredService
from .stats_translator                  import translate_gathered_stats

log = logging.getLogger()


# --------------------------------------------------------------------------------
class _StatsSender(SenderBase[StatsRequestDto, StatsResponseDto]):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.statistics.get", StatsRequestDto, StatsResponseDto)

    async def send(self, stat_type: str = "gathered"):
        return await self.send_data(StatsRequestDto(type=stat_type))

    async def get_gathered(self) -> StatsResponseDto:
        return await self.send_data(StatsRequestDto(type="gathered"))


# --------------------------------------------------------------------------------
def _make_client(service: DiscoveredService) -> Optional[ClientBase]:
    if service.protocol == "udp":
        return UDPClient(server_host=service.host, server_port=service.port)
    if service.protocol == "tcp":
        return TransientTCPClient(server_host=service.host, server_port=service.port)
    if service.protocol == "uds":
        return TransientUDSClient(server_path=service.path)
    return None


# --------------------------------------------------------------------------------
class _ServiceScrapeTarget:
    def __init__(self, service: DiscoveredService):
        self.service = service
        self.key     = f"{service.name}-{service.instance}"
        self.client  = _make_client(service)
        self.sender  = _StatsSender(self.client) if self.client else None
        self.healthy = False


# --------------------------------------------------------------------------------
class EkosisPrometheusScraper:
    def __init__(self, services: List[DiscoveredService]):
        config              = AppConfiguration()
        self._pushgateway   = config.extra.get("PUSHGATEWAY")
        self._job_name      = config.extra.get("JOB_NAME", f"{config.name}-{config.instance}")
        self._poll_interval = config.stats_keeper.gather_period
        self._targets       = [_ServiceScrapeTarget(s) for s in services]

    # --------------------------------------------------------------------------------
    async def run(self):
        log.info(f"Prometheus scraper started. Pushgateway: [{self._pushgateway}] Poll interval: [{self._poll_interval}s]")
        log.info(f"Monitoring {len(self._targets)} service(s): {[t.key for t in self._targets]}")
        while True:
            await asyncio.sleep(self._poll_interval)
            await self._scrape_and_push()

    # --------------------------------------------------------------------------------
    async def _scrape_and_push(self):
        registry     = CollectorRegistry()
        health_gauge = Gauge(
            "ekosis_service_health",
            "1 if service responded to last stats poll, 0 otherwise",
            ["service", "instance"],
            registry = registry,
        )

        for target in self._targets:
            if target.sender is None:
                log.warning(f"No client available for [{target.key}] -- skipping")
                continue

            try:
                response = await target.sender.get_gathered()
                stats    = response.statistics
                target.healthy = True
                health_gauge.labels(service=target.service.name, instance=target.service.instance).set(1)

                for metric_name, value, labels in translate_gathered_stats(stats, target.service.name, target.service.instance):
                    gauge = registry._names_to_collectors.get(metric_name)
                    if gauge is None:
                        gauge = Gauge(metric_name, metric_name, list(labels.keys()), registry=registry)
                    gauge.labels(**labels).set(value)

            except Exception as e:
                target.healthy = False
                health_gauge.labels(service=target.service.name, instance=target.service.instance).set(0)
                log.warning(f"Failed to scrape [{target.key}]: {e}")

        try:
            push_to_gateway(self._pushgateway, job=self._job_name, registry=registry)
        except Exception as e:
            log.error(f"Failed to push to Pushgateway [{self._pushgateway}]: {e}")
