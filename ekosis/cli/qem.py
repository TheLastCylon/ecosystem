import asyncio
import argparse

from .shared_functions import get_client, print_error, any_true_check
from .shared_queue_argument_parser import setup_queued_endpoint_options, argument_parser
from .senders.queued_endpoint_management import (
    EcoQueuedHandlerDataSender,
    EcoQueuedHandlerReceivingPauseSender,
    EcoQueuedHandlerProcessingPauseSender,
    EcoQueuedHandlerAllPauseSender,
    EcoQueuedHandlerReceivingUnPauseSender,
    EcoQueuedHandlerProcessingUnPauseSender,
    EcoQueuedHandlerAllUnPauseSender,
    EcoQueuedHandlerErrorsGetFirst10Sender,
    EcoQueuedHandlerErrorsReprocessAllSender,
    EcoQueuedHandlerErrorsClearSender,
    EcoQueuedHandlerErrorsReprocessOneSender,
    EcoQueuedHandlerErrorsPopRequestSender,
    EcoQueuedHandlerErrorsInspectRequestSender
)

from ..clients import ClientBase

# --------------------------------------------------------------------------------
setup_queued_endpoint_options()

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
        await EcoQueuedHandlerDataSender(client).send(route_key)
        return

    if command_line_args.pause_receiving:
        await EcoQueuedHandlerReceivingPauseSender(client).send(route_key)
        return
    if command_line_args.pause_processing:
        await EcoQueuedHandlerProcessingPauseSender(client).send(route_key)
        return
    if command_line_args.pause_all:
        await EcoQueuedHandlerAllPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_receiving:
        await EcoQueuedHandlerReceivingUnPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_processing:
        await EcoQueuedHandlerProcessingUnPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_all:
        await EcoQueuedHandlerAllUnPauseSender(client).send(route_key)
        return
    if command_line_args.error_10:
        await EcoQueuedHandlerErrorsGetFirst10Sender(client).send(route_key)
        return
    if command_line_args.reprocess_all:
        await EcoQueuedHandlerErrorsReprocessAllSender(client).send(route_key)
        return
    if command_line_args.clear:
        await EcoQueuedHandlerErrorsClearSender(client).send(route_key)
        return

    if not command_line_args.request_uid:
        print_error(argument_parser, "--request_uid required!")
        return

    request_uid = command_line_args.request_uid

    if command_line_args.reprocess_one:
        await EcoQueuedHandlerErrorsReprocessOneSender(client).send(route_key, request_uid)
        return
    if command_line_args.inspect_request:
        await EcoQueuedHandlerErrorsInspectRequestSender(client).send(route_key, request_uid)
        return
    if command_line_args.pop_request:
        await EcoQueuedHandlerErrorsPopRequestSender(client).send(route_key, request_uid)
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
