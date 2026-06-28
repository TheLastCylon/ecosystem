#!/usr/bin/env bash
set -e

SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
EKOCPP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BUILD_DIR="$EKOCPP_DIR/build"
PYTHON_EXAMPLES="$(dirname "$EKOCPP_DIR")/examples/observable_fun"

echo "EKOCPP_DIR     : $EKOCPP_DIR"
echo "BUILD_DIR      : $BUILD_DIR"
echo "PYTHON_EXAMPLES: $PYTHON_EXAMPLES"

# Machine level configurations
export ECOENV_BUFFER_DIR=/tmp/observable_fun_cpp/queues
export ECOENV_LOG_DIR=/tmp/observable_fun_cpp
export ECOENV_STAT_GP=60
export ECOENV_STAT_HL=60

# Observability -- OTLP HTTP traces endpoint
export ECOENV_EXTRA_OTLP_TRACES_ENDPOINT=http://<YOUR_HOSTNAME>:4318/v1/traces
export ECOENV_EXTRA_EKOCPP_OTLP_METRICS_0_OTLP_METRICS_ENDPOINT=http://<YOUR_HOSTNAME>:9090/api/v1/otlp/v1/metrics

# Server listen addresses -- instance level
export ECOENV_UDP_FORTUNES_0=127.0.0.1:8100
export ECOENV_UDP_JOKER_0=127.0.0.1:8200
export ECOENV_UDP_LOTTERY_0=127.0.0.1:8300
export ECOENV_UDP_MAGIC_EIGHT_BALL_0=127.0.0.1:8400
export ECOENV_UDP_TIME_REPORTER_0=127.0.0.1:8500
export ECOENV_UDP_ROUTER_0=127.0.0.1:8600
export ECOENV_UDP_TRACKER_0=127.0.0.1:8700

# Data files -- point at the Python example data (same content, no duplication)
export ECOENV_EXTRA_FORTUNES_0_FORTUNES_DATA_FILE="$PYTHON_EXAMPLES/fortunes/data.txt"
export ECOENV_EXTRA_JOKER_0_JOKER_DATA_FILE="$PYTHON_EXAMPLES/joker/dad_jokes.txt"

# Tracker database
export ECOENV_EXTRA_TRACKER_0_DB_FILE=/tmp/observable_fun_cpp/tracker-0-database.sqlite

echo "Creating buffer dir: $ECOENV_BUFFER_DIR"
mkdir -p "$ECOENV_BUFFER_DIR"

echo "Creating log dir   : $ECOENV_LOG_DIR"
mkdir -p "$ECOENV_LOG_DIR"

# Start all services
"$BUILD_DIR/examples/observable_fun/fortunes"         -i 0 -lfo &
"$BUILD_DIR/examples/observable_fun/joker"            -i 0 -lfo &
"$BUILD_DIR/examples/observable_fun/lottery"          -i 0 -lfo &
"$BUILD_DIR/examples/observable_fun/magic_eight_ball" -i 0 -lfo &
"$BUILD_DIR/examples/observable_fun/time_reporter"    -i 0 -lfo &
"$BUILD_DIR/examples/observable_fun/router"           -i 0 -lfo &
"$BUILD_DIR/examples/observable_fun/tracker"          -i 0 -lfo &
"$BUILD_DIR/otlp_metrics/ekocpp_otlp_metrics"         -i 0

echo "All services started."
