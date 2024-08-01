import sys
import argparse

from typing import List, Tuple

from ..clients import TransientTCPClient, UDPClient, TransientUDSClient, ClientBase

# --------------------------------------------------------------------------------
def make_tcp_udp_host_port(server_details: str) -> Tuple[str, int]:
    host, port = server_details.split(":")
    if not host:
        print_error(f"Could not extract host from command: {server_details}")
    if not port:
        print_error(f"Could not extract port from command: {server_details}")
    return host, int(port)

# --------------------------------------------------------------------------------
def get_client(command_line_args: argparse.Namespace) -> ClientBase:
    if command_line_args.server_type == "tcp":
        host, port = make_tcp_udp_host_port(command_line_args.server_details)
        client     = TransientTCPClient(host, port)
    elif command_line_args.server_type == "udp":
        host, port = make_tcp_udp_host_port(command_line_args.server_details)
        client     = UDPClient(host, port)
    else:
        client = TransientUDSClient(command_line_args.server_details)
    return client

# --------------------------------------------------------------------------------
def print_error(argument_parser: argparse.ArgumentParser, message: str):
    print("================================================================================")
    print(f"ERROR: {message}")
    print("--------------------------------------------------------------------------------")
    argument_parser.print_help()
    print("================================================================================")
    sys.exit(1)

# --------------------------------------------------------------------------------
def any_true_check(list_to_check: List[bool]) -> bool:
    for list_item in list_to_check:
        if list_item:
            return True
    return False
