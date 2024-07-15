import asyncio
from typing import Tuple, List

from .argument_parser import command_line_args, argument_parser
from .senders.eco_statistics_get import EcoStatisticsGetSender
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


from ..clients import TCPClient, UDPClient, UDSClient, ClientBase


# --------------------------------------------------------------------------------
def make_tcp_udp_host_port(request: str) -> Tuple[str, int]:
    host, port = request.split(":")
    if not host:
        print(f"Could not extract host from command: {request}")

    if not port:
        print(f"Could not extract port from command: {request}")

    return host, int(port)


# --------------------------------------------------------------------------------
def get_client() -> ClientBase:
    if command_line_args.server_type == "tcp":
        host, port = make_tcp_udp_host_port(command_line_args.server_details)
        client     = TCPClient(host, port)
    elif command_line_args.server_type == "udp":
        host, port = make_tcp_udp_host_port(command_line_args.server_details)
        client     = UDPClient(host, port)
    else:
        client = UDSClient(command_line_args.server_details)

    return client


# --------------------------------------------------------------------------------
def print_error(message: str):
    print("================================================================================")
    print(f"ERROR: {message}")
    print("--------------------------------------------------------------------------------")
    argument_parser.print_help()
    print("================================================================================")


# --------------------------------------------------------------------------------
def any_true_check(list_to_check: List[bool]) -> bool:
    for list_item in list_to_check:
        if list_item:
            return True
    return False


# --------------------------------------------------------------------------------
async def do_endpoint_action(client: ClientBase, route_key: str):
    if command_line_args.data or not any_true_check([
        command_line_args.data,
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
        print_error("--request_uid required!")
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
async def do_sender_action(client: ClientBase, route_key: str):
    if (command_line_args.pause_receiving   or
        command_line_args.pause_processing  or
        command_line_args.unpause_receiving or
        command_line_args.unpause_processing):
        print_error("Pause and UN-Pause for receiving and processing, is only for queued endpoints!")

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
        print_error("--request_uid required!")
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
async def do_queue_action(client: ClientBase):
    if not command_line_args.route_key:
        print_error("--route_key required!")
        return

    route_key = command_line_args.route_key

    if command_line_args.action == "qem":
        await do_endpoint_action(client, route_key)
    else:
        await do_sender_action(client, route_key)


# --------------------------------------------------------------------------------
async def main():
    client = get_client()
    if command_line_args.action != "stat":
        await do_queue_action(client)
    else:
        await EcoStatisticsGetSender(client).send(command_line_args.statistics_type)

asyncio.run(main())
