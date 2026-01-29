from pydantic import BaseModel as PydanticBaseModel


# --------------------------------------------------------------------------------
class BufferedEndpointResponseDTO(PydanticBaseModel):
    uid: str
