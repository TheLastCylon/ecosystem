from ekosis.application_base import ApplicationBase

from .service_discovery import discover_local_services
from .scraper            import EkosisPrometheusScraper

# --------------------------------------------------------------------------------
class EkosisPrometheusApp(ApplicationBase):
    def __init__(self):
        super().__init__()
        self._services = discover_local_services()
        self._scraper  = EkosisPrometheusScraper(self._services)

    async def setup_tasks(self, tasks: list):
        tasks.append(self._scraper.run())

# --------------------------------------------------------------------------------
def main():
    with EkosisPrometheusApp() as app:
        app.start()

# --------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
