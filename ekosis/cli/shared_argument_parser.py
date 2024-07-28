import argparse

from .argparse_formatter import EcosystemArgparseFormatter

argument_parser: argparse.ArgumentParser = argparse.ArgumentParser(formatter_class=EcosystemArgparseFormatter)

argument_parser.add_argument(
    "-st", "--server_type",
    required = True,
    choices  = ["tcp", "udp", "uds"],
    type     = str,
    default  = None,
    help     = "The type of server you want to interact with."
)

argument_parser.add_argument(
    "-sd", "--server_details",
    metavar  = "<server details>",
    required = True,
    default  = None,
    help     = "Connection details for the server.\n"
               "- For TCP or UDP:\n"
               "- : This should be a string in the format [HOST:PORT].\n"
               "- For UDS:\n"
               "- : This should be a path to the socket file."
)
