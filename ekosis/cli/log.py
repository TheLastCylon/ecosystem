import asyncio
import argparse

from .shared_functions import get_client
from .shared_argument_parser import argument_parser

from .senders.log import EcoLogLevelSender, EcoLogBufferSender

argument_parser.add_argument(
    "-l",
    "--level",
    required = False,
    choices  = ['debug', 'info', 'warn', 'error', 'critical'],
    type     = str,
    default  = None,
    help     = "Set the current log level.\n"
               "(default = None)"
)

argument_parser.add_argument(
    "-b",
    "--buff_size",
    required = False,
    type     = int,
    default  = None,
    help     = "Set the current file log buffer size.\n"
               "(default = None)"
)

command_line_args: argparse.Namespace = argument_parser.parse_args()

# --------------------------------------------------------------------------------
async def main():
    client = get_client(command_line_args)
    if command_line_args.level is not None:
        await EcoLogLevelSender(client).send(command_line_args.level)
    if command_line_args.buff_size is not None:
        await EcoLogBufferSender(client).send(command_line_args.buff_size)

# --------------------------------------------------------------------------------
asyncio.run(main())
