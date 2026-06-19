from contextvars import ContextVar, Token
from typing import Optional

from ..data_transfer_objects import SpanKey

# Internal only -- NOT part of the public API.
#
# The formal, documented way a user obtains span_key is by declaring it in
# an endpoint's parameter list (accepted_parameters delivers it). This exists
# purely so framework code -- the OtlpFormatter, future ekosis-otlp-traces
# child-span helpers -- can read "the span_key of the request currently being
# handled" without it being threaded through every call signature in between.
#
# Scoped per-asyncio-Task, not per-thread: ServerBase is single-threaded, and
# ContextVar is the primitive that isolates concurrent Tasks on one event
# loop from each other, the same way thread-local storage isolates threads.
_current_span_key: ContextVar[Optional[SpanKey]] = ContextVar("current_span_key", default=None)

# --------------------------------------------------------------------------------
def _set_current_span_key(span_key: Optional[SpanKey]) -> Token:
    return _current_span_key.set(span_key)

# --------------------------------------------------------------------------------
def _reset_current_span_key(token: Token):
    _current_span_key.reset(token)

# --------------------------------------------------------------------------------
def _get_current_span_key() -> Optional[SpanKey]:
    return _current_span_key.get()
