import asyncio
import argparse

from .shared_functions import get_client, print_error, any_true_check
from .shared_queue_argument_parser import setup_buffered_endpoint_options, argument_parser
from .senders.buffered_endpoint_management import (
    EcoBufferedHandlerDataSender,
    EcoBufferedHandlerReceivingPauseSender,
    EcoBufferedHandlerProcessingPauseSender,
    EcoBufferedHandlerAllPauseSender,
    EcoBufferedHandlerReceivingUnPauseSender,
    EcoBufferedHandlerProcessingUnPauseSender,
    EcoBufferedHandlerAllUnPauseSender,
    EcoBufferedHandlerErrorsGetFirst10Sender,
    EcoBufferedHandlerErrorsReprocessAllSender,
    EcoBufferedHandlerErrorsClearSender,
    EcoBufferedHandlerErrorsReprocessOneSender,
    EcoBufferedHandlerErrorsPopRequestSender,
    EcoBufferedHandlerErrorsInspectRequestSender
)

from ..clients import ClientBase

# --------------------------------------------------------------------------------
setup_buffered_endpoint_options()

command_line_args: argparse.Namespace = argument_parser.parse_args()

# --------------------------------------------------------------------------------
async def do_endpoint_action(client: ClientBase, route_key: str):
    if not any_true_check([
        command_line_args.pause_receiving,
        command_line_args.pause_processing,
        command_line_args.pause_all,
        command_line_args.unpause_receiving,
        command_line_args.unpause_processing,
        command_line_args.unpause_all,
        command_line_args.error_10,
        command_line_args.reprocess_all,
        command_line_args.clear,
        command_line_args.reprocess_one,
        command_line_args.inspect_request,
        command_line_args.pop_request,
    ]):
        await EcoBufferedHandlerDataSender(client).send(route_key)
        return

    if command_line_args.pause_receiving:
        await EcoBufferedHandlerReceivingPauseSender(client).send(route_key)
        return
    if command_line_args.pause_processing:
        await EcoBufferedHandlerProcessingPauseSender(client).send(route_key)
        return
    if command_line_args.pause_all:
        await EcoBufferedHandlerAllPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_receiving:
        await EcoBufferedHandlerReceivingUnPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_processing:
        await EcoBufferedHandlerProcessingUnPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_all:
        await EcoBufferedHandlerAllUnPauseSender(client).send(route_key)
        return
    if command_line_args.error_10:
        await EcoBufferedHandlerErrorsGetFirst10Sender(client).send(route_key)
        return
    if command_line_args.reprocess_all:
        await EcoBufferedHandlerErrorsReprocessAllSender(client).send(route_key)
        return
    if command_line_args.clear:
        await EcoBufferedHandlerErrorsClearSender(client).send(route_key)
        return

    if not command_line_args.request_uid:
        print_error(argument_parser, "--request_uid required!")
        return

    request_uid = command_line_args.request_uid

    if command_line_args.reprocess_one:
        await EcoBufferedHandlerErrorsReprocessOneSender(client).send(route_key, request_uid)
        return
    if command_line_args.inspect_request:
        await EcoBufferedHandlerErrorsInspectRequestSender(client).send(route_key, request_uid)
        return
    if command_line_args.pop_request:
        await EcoBufferedHandlerErrorsPopRequestSender(client).send(route_key, request_uid)
        return

# --------------------------------------------------------------------------------
async def main():
    client = get_client(command_line_args)

    if not command_line_args.route_key:
        print_error(argument_parser, "--route_key required!")
        return

    route_key = command_line_args.route_key

    await do_endpoint_action(client, route_key)

# --------------------------------------------------------------------------------
asyncio.run(main())
