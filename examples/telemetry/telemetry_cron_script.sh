# --------------------------------------------------------------------------------
# This is where you'll need to put the information for your instance of InfluxDB.
# --------------------------------------------------------------------------------
# INFLUX_URL=#<<Your Influx URL here>> On a local installation that defaults to http://localhost:8086)
# INFLUX_ORG=#<<Your Influx Organisation Name Here>>
# INFLUX_BUCKET=#<<Your Bucket Name Here>>
# INFLUX_TOKEN=#<<Your Influx API Token Here.>> WARNING: In a production environment, this should not be hard coded, set it using an environment variable.>>

# --------------------------------------------------------------------------------
# I have to do the next two lines on my system, you might not need to.
# It sets up the path to pipenv and the python version I want to use.
# --------------------------------------------------------------------------------
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:/home/linuxbrew/.linuxbrew/bin:$PATH"

# --------------------------------------------------------------------------------
# With what follows, I get the directory you cloned this repository into, using
# the location of the script, on your system.
# --------------------------------------------------------------------------------
CURRENT_DIR="$(pwd)"
ABSOLUTE_SCRIPT_PATH="$(readlink -f "${0}")"
SCRIPT_DIR="$(dirname "$ABSOLUTE_SCRIPT_PATH")"
EXAMPLES_DIR="$(dirname "$SCRIPT_DIR")"
REPOSITORY_DIR="$(dirname "$EXAMPLES_DIR")"

cd "$REPOSITORY_DIR"

# --------------------------------------------------------------------------------
# Here we log some data to a file named `cron_run_time.txt`
# Just in case we need to debug a few things.
# --------------------------------------------------------------------------------
echo "DATE          : "`date`               > "cron_run_time.txt"
echo "PIPENV VERSION: "`pipenv --version`  >> "cron_run_time.txt"
echo "PYTHON VERSION: "`python3 --version` >> "cron_run_time.txt"
echo "PIP3   VERSION: "`pip3 --version`    >> "cron_run_time.txt"

# --------------------------------------------------------------------------------
# And here we run the python script that gets the telemetry data from an Ecosystem
# application, and writes it to InfluxDb.
#
# We run it for each of the components in the Fun Factory example system.
#
# Note that the output of each command is re-directed to a file named "cron_log.txt".
# Again, just in case we need to do some debugging.
# --------------------------------------------------------------------------------

# Fortunes
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8100 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

# Joker
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8200 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

# Lottery
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8300 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

# Magic 8-ball
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8400 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

# Time reporter
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8500 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

# Router
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8600 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

# Tracker
pipenv run python3 -m examples.telemetry.telemetry_example -st tcp -sd 127.0.0.1:8700 -ifu $INFLUX_URL -ifo $INFLUX_ORG -ifb $INFLUX_BUCKET -ift $INFLUX_TOKEN >> cron_log.txt 2>&1

cd "$CURRENT_DIR"
