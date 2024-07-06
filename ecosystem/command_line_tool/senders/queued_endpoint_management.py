from .queued_management_sender_base import QueueManagementSenderBase, QueueManagementItemSenderBase

from ...clients import ClientBase


# --------------------------------------------------------------------------------
class EcoQueuedHandlerDataSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.data")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerReceivingPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.receiving.pause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerProcessingPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.processing.pause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerAllPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.all.pause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerReceivingUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.receiving.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerProcessingUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.processing.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerAllUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.all.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsGetFirst10Sender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.get_first_10")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsReprocessAllSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.reprocess.all")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsClearSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.clear")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsReprocessOneSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.reprocess.one")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsPopRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.pop_request")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsInspectRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.inspect_request")
