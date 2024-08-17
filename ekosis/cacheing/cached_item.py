from typing import Any

# --------------------------------------------------------------------------------
class CachedItem:
    __slots__ = ('empty', 'next', 'previous', 'key', 'value')

    def __init__(self):
        self.empty    : bool         = True
        self.previous : 'CachedItem' = None
        self.next     : 'CachedItem' = None
        self.key      : Any          = None
        self.value    : Any          = None
