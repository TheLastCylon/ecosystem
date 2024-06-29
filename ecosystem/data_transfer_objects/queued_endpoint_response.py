from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class QueuedEndpointResponseDTO(PydanticBaseModel):
    uid: str
