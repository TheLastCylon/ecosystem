from .queue_management_sender_base import QueueManagementSenderBase, QueueManagementItemSenderBase

from ...clients import ClientBase


# --------------------------------------------------------------------------------
class EcoBufferedHandlerDataSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.data")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerReceivingPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.receiving.pause")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerProcessingPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.processing.pause")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerAllPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.all.pause")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerReceivingUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.receiving.unpause")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerProcessingUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.processing.unpause")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerAllUnPauseSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.all.unpause")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerErrorsGetFirst10Sender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.errors.get_first_10")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerErrorsReprocessAllSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.errors.reprocess.all")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerErrorsClearSender(QueueManagementSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.errors.clear")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerErrorsReprocessOneSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.errors.reprocess.one")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerErrorsPopRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.errors.pop_request")


# --------------------------------------------------------------------------------
class EcoBufferedHandlerErrorsInspectRequestSender(QueueManagementItemSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.buffered_handler.errors.inspect_request")
