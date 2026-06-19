CURRENT_DIR="$(pwd)"
SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"
REPOSITORY_DIR="$(dirname "$EXAMPLES_DIR")"
VENV="$REPOSITORY_DIR/.venv/bin/python"

echo "REPOSITORY_DIR: $REPOSITORY_DIR"

cd "$REPOSITORY_DIR"

export ECOENV_BUFFER_DIR=/tmp/fun_factory/queues
export ECOENV_LOG_DIR=/tmp/fun_factory
export ECOENV_STAT_GP=60
export ECOENV_STAT_HL=60

echo "Creating buffered communications dir: $ECOENV_BUFFER_DIR"
mkdir -p "$ECOENV_BUFFER_DIR"

echo "Creating log dir: $ECOENV_LOG_DIR"
mkdir -p "$ECOENV_LOG_DIR"

# Extra configs
export ECOENV_EXTRA_TRACKER_0_DB_FILE="$ECOENV_LOG_DIR/tracker-0-database.sqlite"

cd "$REPOSITORY_DIR"

# Start the system
$VENV -m examples.fun_factory.fortunes.fortune                  -i 0 -lfo &
$VENV -m examples.fun_factory.joker.joker                       -i 0 -lfo &
$VENV -m examples.fun_factory.lottery.lottery                   -i 0 -lfo &
$VENV -m examples.fun_factory.magic_eight_ball.magic_eight_ball -i 0 -lfo &
$VENV -m examples.fun_factory.time_reporter.time_reporter       -i 0 -lfo &
$VENV -m examples.fun_factory.router.router                     -i 0 -lfo &
$VENV -m examples.fun_factory.tracker.tracker                   -i 0 -lfo &

cd "$CURRENT_DIR"
