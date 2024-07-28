import asyncio
import argparse

from .shared_functions import get_client
from .shared_argument_parser import argument_parser

from .senders.statistics import EcoStatisticsGetSender

argument_parser.add_argument(
    "-type", "--type",
    required = False,
    choices  = ["current", "gathered", "full"],
    type     = str,
    default  = "current",
    help     = "The statistics type you want to retrieve.\n"
               "- 'current': The current statistical period.\n"
               "- 'gathered': The last gathered statistical period.\n"
               "- 'full': The full gathered statistics history.\n"
               " (default = 'current')"
)

command_line_args: argparse.Namespace = argument_parser.parse_args()

# --------------------------------------------------------------------------------
async def main():
    client = get_client(command_line_args)
    await EcoStatisticsGetSender(client).send(command_line_args.type)

# --------------------------------------------------------------------------------
asyncio.run(main())
