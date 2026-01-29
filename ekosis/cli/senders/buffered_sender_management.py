from .queue_management_sender_base import QueueManagementSenderBase, QueueManagementItemSenderBase

from ...clients import ClientBase


# --------------------------------------------------------------------------------
class EcoBufferedSenderDataSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.data")


# --------------------------------------------------------------------------------
class EcoBufferedSenderSendProcessPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.send_process.pause")


# --------------------------------------------------------------------------------
class EcoBufferedSenderSendProcessUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.send_process.unpause")


# --------------------------------------------------------------------------------
class EcoBufferedSenderErrorsGetFirst10Sender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.errors.get_first_10")


# --------------------------------------------------------------------------------
class EcoBufferedSenderErrorsReprocessAllSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.errors.reprocess.all")


# --------------------------------------------------------------------------------
class EcoBufferedSenderErrorsClearSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.errors.clear")


# --------------------------------------------------------------------------------
class EcoBufferedSenderErrorsReprocessOneSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.errors.reprocess.one")


# --------------------------------------------------------------------------------
class EcoBufferedSenderErrorsPopRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.errors.pop_request")


# --------------------------------------------------------------------------------
class EcoBufferedSenderErrorsInspectRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_sender.errors.inspect_request")
