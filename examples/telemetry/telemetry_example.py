import os.path
import socket
import datetime
import asyncio

from typing import Dict, Tuple

import influxdb_client
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from ecosystem.clients import TCPClient, UDPClient, UDSClient, ClientBase
from ecosystem.sending.sender import sender
from ecosystem.data_transfer_objects.statistics import StatsRequestDto, StatsResponseDto
from ecosystem.util.utility_functions import (
    is_valid_hostname,
    is_valid_port_number,
    flatten_dictionary,
    get_machine_hostname,
    is_valid_url
)

from .argument_parser import command_line_args, argument_parser

# ================================================================================
# First we do the global setup.

# Global variables: For use with Influx.
# --------------------------------------------------------------------------------
INFLUX_URL       : str                      = command_line_args.influx_url    # The influx URL to use
INFLUX_BUCKET    : str                      = command_line_args.influx_bucket # The influx bucket
INFLUX_ORG       : str                      = command_line_args.influx_org    # The influx organization
INFLUX_TOKEN     : str                      = command_line_args.influx_token  # The influx API token
INFLUX_API_WRITER: influxdb_client.WriteApi = None                            # Will be set to the influx DB writer, we'll need.

# Global variables: for use with the data points
# --------------------------------------------------------------------------------
MACHINE_HOSTNAME    : str = ""   # Will be set to the hostname of the machine the Ecosystem application is running on.
APPLICATION_NAME    : str = ""   # Will be set to the Ecosystem application name
APPLICATION_INSTANCE: str = ""   # Will be set to the Ecosystem application instance

# Global variables: for use with Ecosystem
# --------------------------------------------------------------------------------
ECO_SYSTEM_APP_CLIENT: ClientBase = None # Will be set to the Ecosystem client we'll use with our sender function

# --------------------------------------------------------------------------------
# Prints errors and help
# --------------------------------------------------------------------------------
def print_error(message: str):
    print("================================================================================")
    print(f"ERROR: {message}")
    print("--------------------------------------------------------------------------------")
    argument_parser.print_help()
    print("================================================================================")
    exit(1)

# --------------------------------------------------------------------------------
# In the event that we want to query telemetry using either TCP or UDP.
# This function validates the configured host and port. If the checks pass, the
# host and port are returned as a Tuple
# --------------------------------------------------------------------------------
def make_tcp_udp_host_port(request: str) -> Tuple[str, int]:
    host, port = request.split(":")
    if not is_valid_hostname(host):
        print_error(f"Invalid hostname specified: {host}")

    if not is_valid_port_number(port):
        print_error(f"Invalid port number specified: {port}")

    return host, int(port)

# --------------------------------------------------------------------------------
# Sets up ECO_SYSTEM_APP_CLIENT with the TCP, UDP or UDS client we'll need.
# It also sets up MACHINE_HOSTNAME, for use in the data points I will be sending
# to Influx.
# --------------------------------------------------------------------------------
def make_ecosystem_client():
    global MACHINE_HOSTNAME, ECO_SYSTEM_APP_CLIENT
    if command_line_args.server_type == "tcp":
        host, port            = make_tcp_udp_host_port(command_line_args.server_details)
        MACHINE_HOSTNAME      = get_machine_hostname(host)
        ECO_SYSTEM_APP_CLIENT = TCPClient(host, port)
    elif command_line_args.server_type == "udp":
        host, port            = make_tcp_udp_host_port(command_line_args.server_details)
        MACHINE_HOSTNAME      = get_machine_hostname(host)
        ECO_SYSTEM_APP_CLIENT = UDPClient(host, port)
    elif command_line_args.server_type == "uds":
        if not os.path.exists(command_line_args.server_type):
            print_error(f"Specified UDS socket file [{command_line_args.server_details}] does not exist.")
        MACHINE_HOSTNAME      = socket.gethostname()
        ECO_SYSTEM_APP_CLIENT = UDSClient(command_line_args.server_details)

# --------------------------------------------------------------------------------
# Sets up INFLUX_API_WRITER with influxdb writer we'll need to write data points
# with.
# --------------------------------------------------------------------------------
def make_influxdb_writer():
    global INFLUX_API_WRITER
    if not is_valid_url(INFLUX_URL):
        print_error(f"Specified InfluxDb URL [{INFLUX_URL}] is invalid.")
    INFLUX_API_WRITER = InfluxDBClient(
        url   = INFLUX_URL,
        token = INFLUX_TOKEN,
        org   = INFLUX_ORG
    ).write_api(write_options=SYNCHRONOUS)

# --------------------------------------------------------------------------------
make_ecosystem_client() # Set up the Ecosystem client we'll use with our sender function
make_influxdb_writer()  # Set up the influx DB writer we'll need

# ================================================================================
# Everything is set by this point.
# Now we declare functions for gathering statistics and writing them.
# --------------------------------------------------------------------------------

# --------------------------------------------------------------------------------
# This is the sender we'll invoke to get statistics from an Ecosystem application
# --------------------------------------------------------------------------------
@sender(ECO_SYSTEM_APP_CLIENT, "eco.statistics.get", StatsResponseDto)
async def get_ecosystem_app_statistics(stat_type: str = "gathered"):
    return StatsRequestDto(type=stat_type)

# --------------------------------------------------------------------------------
# This function uses the sender we defined above, to get telemetry from an
# Ecosystem application.
#
# It also verifies that we did get telemetry for the last gathering period.
# If the check fails, it will try to get telemetry for the CURRENT gathering period.
#
# This check exists because it is possible for an application to simply not have
# been running long enough, for it to have gathered statistics.
# --------------------------------------------------------------------------------
async def get_statistics():
    response: StatsResponseDto = await get_ecosystem_app_statistics()
    data                       = response.model_dump()
    statistics                 = data["statistics"]

    if 'uptime' not in statistics.keys():
        response   = await get_ecosystem_app_statistics('current')
        data       = response.model_dump()
        statistics = data["statistics"]

    return statistics

# --------------------------------------------------------------------------------
# This create a data point, with standard tags I want for each of the data points
# I send to InfluxDB
# --------------------------------------------------------------------------------
def make_base_data_point() -> Point:
    data_point = Point("ecosystem_statistics")
    data_point.tag("eco_host_name"   , MACHINE_HOSTNAME)
    data_point.tag("eco_app_name"    , APPLICATION_NAME)
    data_point.tag("eco_app_instance", APPLICATION_INSTANCE)
    return data_point

# --------------------------------------------------------------------------------
# This does the writing of data points, to influxdb
# --------------------------------------------------------------------------------
async def write_influx_data(data_point: Point):
    INFLUX_API_WRITER.write(
        bucket = INFLUX_BUCKET,
        org    = INFLUX_ORG,
        record = data_point
    )

# --------------------------------------------------------------------------------
# With this, I write the number of times each endpoint of an Ecosystem application
# has been called, to InfluxDb.
# Note that I filter out the standard Ecosystem endpoints for the application.
# --------------------------------------------------------------------------------
async def log_endpoint_call_counts(
    endpoint_call_counts: Dict[str, int],
    time_to_log         : str
):
    for key, value in endpoint_call_counts.items():
        if not key.startswith("eco."): # Here I filter out the standard Ecosystem endpoints
            data_point = make_base_data_point()

            data_point.tag  ("endpoint_called", key.replace('.call_count', ''))
            data_point.field("call_count"     , value)

            data_point.time(time_to_log)
            await write_influx_data(data_point)

# --------------------------------------------------------------------------------
# With this I write each of the queued ENDPOINT database sizes.
# --------------------------------------------------------------------------------
async def log_queued_endpoint_sizes(
    queued_endpoint_sizes: Dict[str, int],
    time_to_log         : str
):
    for key, value in queued_endpoint_sizes.items():
        data_point = make_base_data_point()

        if key.endswith("pending"):
            data_point.tag("queued_endpoint", key.replace('.pending', ''))
            data_point.field('pending'      , value)
        else:
            data_point.tag("queued_endpoint", key.replace('.error', ''))
            data_point.field('error'        , value)

        data_point.time(time_to_log)
        await write_influx_data(data_point)

# --------------------------------------------------------------------------------
# With this I write each of the queued SENDER database sizes.
# --------------------------------------------------------------------------------
async def log_queued_sender_sizes(
    queued_endpoint_sizes: Dict[str, int],
    time_to_log         : str
):
    for key, value in queued_endpoint_sizes.items():
        data_point = make_base_data_point()

        if key.endswith("pending"):
            data_point.tag("queued_sender", key.replace('.pending', ''))
            data_point.field('pending'    , value)
        else:
            data_point.tag("queued_sender", key.replace('.error', ''))
            data_point.field('error'      , value)

        data_point.time(time_to_log)
        await write_influx_data(data_point)

# --------------------------------------------------------------------------------
# And here's the main function.
# --------------------------------------------------------------------------------
async def main():
    global APPLICATION_NAME, APPLICATION_INSTANCE
    try:
        # We get the statistics
        statistics            = await get_statistics()

        # Set up the application name and instance for use in the data points
        APPLICATION_NAME      = statistics['application']['name']
        APPLICATION_INSTANCE  = statistics['application']['instance']

        # Set up the timestamp we'll use with the data points
        timestamp             = statistics['timestamp']
        time_to_log           = datetime.datetime.fromtimestamp(timestamp).isoformat()

        # flatten the various telemetry dictionaries for use in our writer functions.
        endpoint_call_counts  = flatten_dictionary(statistics['endpoint_call_counts'])
        queued_endpoint_sizes = flatten_dictionary(statistics['queued_endpoint_sizes']) if 'queued_endpoint_sizes' in statistics.keys() else None
        queued_sender_sizes   = flatten_dictionary(statistics['queued_sender_sizes'])   if 'queued_sender_sizes'   in statistics.keys() else None

        # And here we call those functions.
        await log_endpoint_call_counts(endpoint_call_counts , time_to_log)

        if queued_endpoint_sizes:
            await log_queued_endpoint_sizes(queued_endpoint_sizes, time_to_log)

        if queued_sender_sizes:
            await log_queued_sender_sizes(queued_sender_sizes  , time_to_log)

    except Exception as e:
        print(f"ERROR: {str(e)}")

# --------------------------------------------------------------------------------
# And last but not least, we invoke the main function using asyncio.run
asyncio.run(main())
