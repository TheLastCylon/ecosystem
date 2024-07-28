from enum import Enum
from pydantic import BaseModel as PydanticBaseModel

class LevelEnum(str, Enum):
    debug    = 'debug'
    info     = 'info'
    warn     = 'warn'
    error    = 'error'
    critical = 'critical'

# --------------------------------------------------------------------------------
class LogLevelRequestDto(PydanticBaseModel):
    level: LevelEnum

# --------------------------------------------------------------------------------
class LogLevelResponseDto(PydanticBaseModel):
    level: str

# --------------------------------------------------------------------------------
class LogBufferRequestDto(PydanticBaseModel):
    size: int

# --------------------------------------------------------------------------------
class LogBufferResponseDto(PydanticBaseModel):
    size: int
