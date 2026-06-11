# Prometheus + Pushgateway + Jaeger + Loki + Grafana

A production-grade observability stack for EcoSystem applications. All components
are free open source software. The stack runs on one central machine via
docker-compose. `alloy` runs as an agent on each machine where your EcoSystem
applications run, shipping logs to the central Loki instance.

---

## Stack components

| Tool        | Role                | Licence    | Port  |
|-------------|---------------------|------------|-------|
| Prometheus  | Metrics storage     | Apache 2.0 | 9090  |
| Pushgateway | Metrics entry point | Apache 2.0 | 9091  |
| Jaeger      | Distributed tracing | Apache 2.0 | 16686 |
| Loki        | Log aggregation     | AGPLv3/BSL | 3100  |
| Grafana     | Dashboards          | AGPLv3/BSL | 3000  |
| Alloy       | Log shipping agent  | Apache 2.0 | --    |

---

## Architecture

```
  App server(s)                          Central stack (one machine)
  -----------------------------          --------------------------------------
  EcoSystem services
    |
    +- traces --------------------------> Jaeger (OTLP HTTP :4318)
    |
    +- metrics --> ekosis-prometheus
    |                  |
    |                  +- push ---------> Pushgateway (:9091)
    |                                          |
    |                                     Prometheus (:9090)
    |
    +- logs --> Alloy agent
                    |
                    +- ship ------------> Loki (:3100)
                                               |
                                          Grafana (:3000)
                                          (queries all three)
```

---

## Prerequisites

- Docker
- Docker Compose v2 (`docker compose`, not `docker-compose`)
- Alloy installed on each app server (see [Alloy setup](#alloy-setup) below)

---

## Stack setup

Create a directory for the stack on your central machine. The structure it expects:

```
observability/
  docker-compose.yml
  prometheus.yml
  loki-config.yml
  alloy-config.alloy        <- not used by docker-compose; lives here for reference
  provisioning/
    datasources/
      datasources.yml
    dashboards/
      dashboards.yml
      ekosis.json           <- EcoSystem Grafana dashboard (from the ecosystem repo)
```

### docker-compose.yml

```yaml
services:

  jaeger:
    image:    jaegertracing/all-in-one:1.57  # PIN -- check for latest stable
    user:     "${UID}:${GID}"                # bind mount -- must match host user ownership
    environment:
      - SPAN_STORAGE_TYPE=badger
      - BADGER_EPHEMERAL=false
      - BADGER_DIRECTORY_VALUE=/badger/data
      - BADGER_DIRECTORY_KEY=/badger/key
    ports:
      - "0.0.0.0:16686:16686"  # Jaeger UI
      - "0.0.0.0:14268:14268"  # Jaeger HTTP
      - "0.0.0.0:4318:4318"    # OTLP HTTP
    volumes:
      - ./jaeger-data:/badger
    networks:
      - monitoring
    restart: unless-stopped

  prometheus:
    image:    prom/prometheus:v2.52.0  # PIN -- check for latest stable
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "0.0.0.0:9090:9090"
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.retention.time=90d
      - --web.enable-lifecycle
    networks:
      - monitoring
    restart: unless-stopped

  pushgateway:
    image:    prom/pushgateway:v1.8.0  # PIN -- check for latest stable
    ports:
      - "0.0.0.0:9091:9091"
    networks:
      - monitoring
    restart: unless-stopped

  loki:
    image:    grafana/loki:3.0.0  # PIN -- check for latest stable
    ports:
      - "0.0.0.0:3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/local-config.yml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yml
    networks:
      - monitoring
    restart: unless-stopped

  grafana:
    image:    grafana/grafana:11.0.0  # PIN -- check for latest stable
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./provisioning:/etc/grafana/provisioning
    ports:
      - "0.0.0.0:3000:3000"
    depends_on:
      - jaeger
      - prometheus
      - loki
    networks:
      - monitoring
    restart: unless-stopped

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  loki-data:
  grafana-data:
```

**Gotcha (`user:`) on Jaeger only:** Jaeger uses a bind mount
(`./jaeger-data:/badger`), so the container process must run as the host user to
own the files. The other services use named volumes, where the image handles its
own permissions, do not add `user:` to them.

Before starting, create the bind mount directory:
```bash
mkdir -p jaeger-data
```

### prometheus.yml

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pushgateway'
    honor_labels: true
    static_configs:
      - targets: ['pushgateway:9091']
```

**Gotcha (`honor_labels: true`):** Without this, Prometheus silently renames the
`instance` label pushed by `ekosis-prometheus` to `exported_instance`. All
label-based filtering in Grafana breaks. Always set `honor_labels: true` on the
pushgateway scrape job.

### loki-config.yml

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory:  /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store:        boltdb-shipper
      object_store: filesystem
      schema:       v11
      index:
        prefix: index_
        period: 24h

limits_config:
  allow_structured_metadata: false

ruler:
  alertmanager_url: http://localhost:9093
```

**Gotcha (`/loki`) not (`/tmp/loki`):** The default Loki config uses `/tmp/loki`
for storage. `/tmp` is ephemeral; all logs are lost on container restart. The
config above uses `/loki`, which maps to the `loki-data` named volume and survives
restarts.

### provisioning/datasources/datasources.yml

```yaml
apiVersion: 1

datasources:

  - name:      Prometheus
    type:      prometheus
    access:    proxy
    url:       http://prometheus:9090
    isDefault: true
    editable:  false

  - name:    Loki
    type:    loki
    access:  proxy
    url:     http://loki:3100
    editable: false

  - name:    Jaeger
    type:    jaeger
    access:  proxy
    url:     http://jaeger:16686
    editable: false
```

Datasource URLs use Docker service names, not `localhost`. This is correct inside
the docker-compose network.

### provisioning/dashboards/dashboards.yml

```yaml
apiVersion: 1

providers:

  - name:            EcoSystem
    type:            file
    disableDeletion: false
    editable:        true
    options:
      path: /etc/grafana/provisioning/dashboards
```

The EcoSystem dashboard JSON (`ekosis.json`) is in the ecosystem repo at
`examples/observable_fun/` -- copy it into `provisioning/dashboards/`.

---

## Starting the stack

```bash
export GRAFANA_ADMIN_PASSWORD=yourpassword
export UID=$(id -u)
export GID=$(id -g)
docker compose up -d
```

`GRAFANA_ADMIN_PASSWORD` must be set, there is no default. `UID` and `GID` are needed for
the Jaeger bind mount.

Grafana, Prometheus, and Jaeger datasources are provisioned automatically on first start.
The EcoSystem dashboard loads automatically if `ekosis.json` is in `provisioning/dashboards/`.

---

## Alloy setup

Alloy is the log shipping agent. Install it on each machine where your EcoSystem
applications run.

### Install

```bash
# Add Grafana apt repository
sudo apt install alloy
```

Full install instructions: https://grafana.com/docs/alloy/latest/get-started/install/linux/

### Configure

Create `/etc/alloy/config.alloy`:

```
local.file_match "ekosis" {
  path_targets = [{"__path__" = "/var/log/ekosis/*.log", job = "ekosis", host = "your-hostname"}]
}

loki.source.file "ekosis" {
  targets    = local.file_match.ekosis.targets
  forward_to = [loki.write.central.receiver]
}

loki.write "central" {
  endpoint {
    url = "http://your-central-stack-host:3100/loki/api/v1/push"
  }
}
```

Update `host` and the Loki `url` for each machine.

**Gotcha (`local.file_match`) is required for glob patterns:** `loki.source.file`
does not expand glob patterns directly. Always use `local.file_match` to resolve
the file list first, then pass its targets to `loki.source.file`.

### Log directory

EcoSystem writes logs to `ECOENV_LOG_DIR` (default `/var/log/ekosis`). Create it
and make it writable by your application user:

```bash
sudo mkdir -p /var/log/ekosis
sudo chown youruser:youruser /var/log/ekosis
```

---

## Connecting your services

Set `ECOENV_EXTRA_JAEGER_ENDPOINT` and `ECOENV_EXTRA_*_PUSHGATEWAY` in your start
script. See `examples/observable_fun/start_observable_fun.sh` for a complete
working example. It shows how to wire `ekosis-jaeger-http` and `ekosis-prometheus`
into a multiservice EcoSystem application alongside the observability stack.
