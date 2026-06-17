CURRENT_DIR="$(pwd)"
SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"
REPOSITORY_DIR="$(dirname "$EXAMPLES_DIR")"
VENV="$REPOSITORY_DIR/.venv/bin/python"
VENV_BIN="$REPOSITORY_DIR/.venv/bin"

echo "REPOSITORY_DIR: $REPOSITORY_DIR"

# Machine level configurations
export ECOENV_BUFFER_DIR=/tmp/observable_fun/queues
export ECOENV_LOG_DIR=/tmp/observable_fun
export ECOENV_STAT_GP=60
export ECOENV_STAT_HL=60

# Observability -- OTLP HTTP traces endpoint
export ECOENV_EXTRA_OTLP_TRACES_ENDPOINT=http://<YOURHOSTNAME_HERE>:4318/v1/traces

# Instance level configurations
export ECOENV_UDP_FORTUNE_0=127.0.0.1:8100
export ECOENV_UDP_JOKER_0=127.0.0.1:8200
export ECOENV_UDP_LOTTERY_0=127.0.0.1:8300
export ECOENV_UDP_MAGIC_EIGHT_BALL_0=127.0.0.1:8400
export ECOENV_UDP_TIME_REPORTER_0=127.0.0.1:8500
export ECOENV_UDP_ROUTER_0=127.0.0.1:8600
export ECOENV_UDP_TRACKER_0=127.0.0.1:8700
export ECOENV_UDP_EKOSIS_PROMETHEUS_0=127.0.0.1:8800

# Observability -- Prometheus Pushgateway (on your host)
export ECOENV_EXTRA_EKOSIS_PROMETHEUS_0_PUSHGATEWAY=http://<YOURHOSTNAME_HERE>:9091

echo "Creating buffered communications dir: $ECOENV_BUFFER_DIR"
mkdir -p "$ECOENV_BUFFER_DIR"

echo "Creating log dir: $ECOENV_LOG_DIR"
mkdir -p "$ECOENV_LOG_DIR"

# Extra configs
export ECOENV_EXTRA_TRACKER_0_DB_FILE=/tmp/observable_fun/tracker-0-database.sqlite

cd "$REPOSITORY_DIR"

# Start the system
$VENV -m examples.observable_fun.fortunes.fortune                  -i 0 -lfo &
$VENV -m examples.observable_fun.joker.joker                       -i 0 -lfo &
$VENV -m examples.observable_fun.lottery.lottery                   -i 0 -lfo &
$VENV -m examples.observable_fun.magic_eight_ball.magic_eight_ball -i 0 -lfo &
$VENV -m examples.observable_fun.time_reporter.time_reporter       -i 0 -lfo &
$VENV -m examples.observable_fun.router.router                     -i 0 -lfo &
$VENV -m examples.observable_fun.tracker.tracker                   -i 0 -lfo &
$VENV_BIN/ekosis_prometheus                                        -i 0 &

cd "$CURRENT_DIR"
