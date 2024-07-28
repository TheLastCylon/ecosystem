import asyncio
import argparse

from .shared_functions import get_client, print_error, any_true_check
from .shared_queue_argument_parser import setup_queued_sender_options, argument_parser
from .senders.queued_sender_management import (
    EcoQueuedSenderDataSender,
    EcoQueuedSenderSendProcessPauseSender,
    EcoQueuedSenderSendProcessUnPauseSender,
    EcoQueuedSenderErrorsGetFirst10Sender,
    EcoQueuedSenderErrorsReprocessAllSender,
    EcoQueuedSenderErrorsClearSender,
    EcoQueuedSenderErrorsReprocessOneSender,
    EcoQueuedSenderErrorsPopRequestSender,
    EcoQueuedSenderErrorsInspectRequestSender,
)

from ..clients import ClientBase

# --------------------------------------------------------------------------------
setup_queued_sender_options()

command_line_args: argparse.Namespace = argument_parser.parse_args()

# --------------------------------------------------------------------------------
async def do_sender_action(client: ClientBase, route_key: str):
    if (command_line_args.pause_receiving   or
        command_line_args.pause_processing  or
        command_line_args.unpause_receiving or
        command_line_args.unpause_processing):
        print_error(argument_parser, "Pause and UN-Pause for receiving and processing, is only for queued endpoints!")

    if command_line_args.data or not any_true_check([
        command_line_args.data,
        command_line_args.pause_all,
        command_line_args.unpause_all,
        command_line_args.error_10,
        command_line_args.reprocess_all,
        command_line_args.clear,
        command_line_args.reprocess_one,
        command_line_args.inspect_request,
        command_line_args.pop_request,
    ]):
        await EcoQueuedSenderDataSender(client).send(route_key)
        return

    if command_line_args.pause_all:
        await EcoQueuedSenderSendProcessPauseSender(client).send(route_key)
        return
    if command_line_args.unpause_all:
        await EcoQueuedSenderSendProcessUnPauseSender(client).send(route_key)
        return
    if command_line_args.error_10:
        await EcoQueuedSenderErrorsGetFirst10Sender(client).send(route_key)
        return
    if command_line_args.reprocess_all:
        await EcoQueuedSenderErrorsReprocessAllSender(client).send(route_key)
        return
    if command_line_args.clear:
        await EcoQueuedSenderErrorsClearSender(client).send(route_key)
        return

    if not command_line_args.request_uid:
        print_error(argument_parser, "--request_uid required!")
        return

    request_uid = command_line_args.request_uid

    if command_line_args.reprocess_one:
        await EcoQueuedSenderErrorsReprocessOneSender(client).send(route_key, request_uid)
        return
    if command_line_args.inspect_request:
        await EcoQueuedSenderErrorsInspectRequestSender(client).send(route_key, request_uid)
        return
    if command_line_args.pop_request:
        await EcoQueuedSenderErrorsPopRequestSender(client).send(route_key, request_uid)
        return

# --------------------------------------------------------------------------------
async def main():
    client = get_client(command_line_args)

    if not command_line_args.route_key:
        print_error(argument_parser, "--route_key required!")
        return

    route_key = command_line_args.route_key

    await do_sender_action(client, route_key)

# --------------------------------------------------------------------------------
asyncio.run(main())
