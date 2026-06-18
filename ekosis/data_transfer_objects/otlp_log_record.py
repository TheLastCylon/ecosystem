from typing import Any, Optional
from pydantic import BaseModel as PydanticBaseModel

# Python stdlib logging levelno -> OTel severity (number, text).
# Neither system has a TRACE band -- debug/info/warn/error/critical map 1:1
# onto 5 of OTel's 6 bands.
_PYTHON_LEVEL_TO_OTEL_SEVERITY = {
    10: (5,  "DEBUG"),
    20: (9,  "INFO"),
    30: (13, "WARN"),
    40: (17, "ERROR"),
    50: (21, "FATAL"),
}

# --------------------------------------------------------------------------------
def severity_for_levelno(levelno: int) -> tuple[int, str]:
    return _PYTHON_LEVEL_TO_OTEL_SEVERITY.get(levelno, (0, "UNSPECIFIED"))

# --------------------------------------------------------------------------------
class OtlpLogRecord(PydanticBaseModel):
    timestamp      : str
    severity_number: int
    severity_text  : str
    body           : str
    attributes     : dict[str, Any] = {}
    trace_id       : Optional[str]  = None
    span_id        : Optional[str]  = None
