from .queued_management_sender_base import QueueManagementSenderBase, QueueManagementItemSenderBase

from ...clients import ClientBase


# --------------------------------------------------------------------------------
class EcoQueuedSenderDataSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.data")


# --------------------------------------------------------------------------------
class EcoQueuedSenderSendProcessPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.send_process.pause")


# --------------------------------------------------------------------------------
class EcoQueuedSenderSendProcessUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.send_process.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedSenderErrorsGetFirst10Sender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.errors.get_first_10")


# --------------------------------------------------------------------------------
class EcoQueuedSenderErrorsReprocessAllSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.errors.reprocess.all")


# --------------------------------------------------------------------------------
class EcoQueuedSenderErrorsClearSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.errors.clear")


# --------------------------------------------------------------------------------
class EcoQueuedSenderErrorsReprocessOneSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.errors.reprocess.one")


# --------------------------------------------------------------------------------
class EcoQueuedSenderErrorsPopRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.errors.pop_request")


# --------------------------------------------------------------------------------
class EcoQueuedSenderErrorsInspectRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_sender.errors.inspect_request")
