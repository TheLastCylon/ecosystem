CURRENT_DIR="$(pwd)"
SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"
REPOSITORY_DIR="$(dirname "$EXAMPLES_DIR")"

echo "REPOSITORY_DIR: $REPOSITORY_DIR"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:/home/linuxbrew/.linuxbrew/bin:$PATH"

# Machine level configurations
export ECOENV_QUEUE_DIR=/tmp
export ECOENV_LOG_DIR=/tmp
export ECOENV_LOG_BUF_SIZE=1500
export ECOENV_STAT_GP=60
export ECOENV_STAT_HL=60

# Instance level configurations
export ECOENV_UDP_FORTUNE_0=127.0.0.1:8100
export ECOENV_UDP_JOKER_0=127.0.0.1:8200
export ECOENV_UDP_LOTTERY_0=127.0.0.1:8300
export ECOENV_UDP_MAGIC_EIGHT_BALL_0=127.0.0.1:8400
export ECOENV_UDP_TIME_REPORTER_0=127.0.0.1:8500
export ECOENV_UDP_ROUTER_0=127.0.0.1:8600
export ECOENV_UDP_TRACKER_0=127.0.0.1:8700

# Extra configs
export ECOENV_EXTRA_TRACKER_0_DB_FILE=/tmp/tracker-0-database.sqlite

cd "$REPOSITORY_DIR"

# Start the system
pipenv run python3 -m examples.proper_fun.fortunes.fortune                  -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.joker.joker                       -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.lottery.lottery                   -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.magic_eight_ball.magic_eight_ball -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.time_reporter.time_reporter       -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.router.router                     -i 0 -lfo &
pipenv run python3 -m examples.proper_fun.tracker.tracker                   -i 0 -lfo &

cd "$CURRENT_DIR"
