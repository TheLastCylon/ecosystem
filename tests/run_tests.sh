CURRENT_DIR="$(pwd)"
SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
REPOSITORY_DIR="$(dirname "$SCRIPT_DIR")"

echo "REPOSITORY_DIR: $REPOSITORY_DIR"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:/home/linuxbrew/.linuxbrew/bin:$PATH"

export ECOENV_QUEUE_DIR=/tmp
export ECOENV_LOG_DIR=/tmp
export ECOENV_LOG_BUF_SIZE=0
export ECOENV_STAT_GP=2
export ECOENV_STAT_HL=2

# Instance level configurations
export ECOENV_TCP_TEST_APP_A_0=127.0.0.1:8888
export ECOENV_UDP_TEST_APP_A_0=127.0.0.1:8889
export ECOENV_UDS_TEST_APP_A_0=/tmp/DEFAULT

export ECOENV_TCP_TEST_APP_B_0=127.0.0.1:9998
export ECOENV_UDP_TEST_APP_B_0=127.0.0.1:9999
export ECOENV_UDS_TEST_APP_B_0=/tmp/DEFAULT

cd "$REPOSITORY_DIR"

pipenv run coverage erase
pipenv run coverage run -p --source=ekosis -m tests.test_app_a.test_app_a -i 0 -lfo &
pipenv run coverage run -p --source=ekosis -m tests.test_app_b.test_app_b -i 0 -lfo &
sleep 1
pipenv run coverage run -p --source=ekosis -m pytest \
  tests/basic_tests.py \
  tests/check_stats_endpoint.py \
  tests/queued_handler_endpoints.py \
  tests/queued_sender_endpoints.py \
  tests/log_manager_endpoints.py \
  tests/error_state_endpoints.py \
  tests/paginated_queue_unit_tests.py \
  tests/utility_functions.py

# pipenv run coverage run -a --source=ekosis -m pytest tests/check_stats_endpoint.py

TEST_APP_A_0_PID="$(cat /tmp/test_app_a-0.lock)"
TEST_APP_B_0_PID="$(cat /tmp/test_app_b-0.lock)"
kill $TEST_APP_A_0_PID $TEST_APP_B_0_PID
pipenv run coverage combine
pipenv run coverage report -m

cd "$CURRENT_DIR"
