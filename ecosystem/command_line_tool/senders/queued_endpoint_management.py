from .queued_endpoint_management_base import QueuedEndpointManagerSenderBase, ErrorQueueManagerBase

from ...clients import ClientBase


# --------------------------------------------------------------------------------
class EcoQueuedHandlerDataSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.data")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerReceivingPauseSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.receiving.pause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerProcessingPauseSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.processing.pause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerAllPauseSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.all.pause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerReceivingUnPauseSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.receiving.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerProcessingUnPauseSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.processing.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerAllUnPauseSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.all.unpause")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsGetFirst10Sender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.get_first_10")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsReprocessAllSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.reprocess.all")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsClearSender(QueuedEndpointManagerSenderBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.clear")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsReprocessOneSender(ErrorQueueManagerBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.reprocess.one")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsPopRequestSender(ErrorQueueManagerBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.pop_request")


# --------------------------------------------------------------------------------
class EcoQueuedHandlerErrorsInspectRequestSender(ErrorQueueManagerBase):
    def __init__(self, client: ClientBase):
        super().__init__(client, "eco.queued_handler.errors.inspect_request")
