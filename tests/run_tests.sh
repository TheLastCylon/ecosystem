CURRENT_DIR="$(pwd)"
SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
REPOSITORY_DIR="$(dirname "$SCRIPT_DIR")"

echo "REPOSITORY_DIR: $REPOSITORY_DIR"

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:/home/linuxbrew/.linuxbrew/bin:$PATH"

cd "$REPOSITORY_DIR"

pipenv run python3 -m tests.test_app.test_app -i 0 -lfo &
sleep 1
pipenv run pytest tests/basic_tests.py

ECHO_PID="$(cat /tmp/test_app-0.lock)"
kill $ECHO_PID

cd "$CURRENT_DIR"
