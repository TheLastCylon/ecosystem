from typing import Any

# --------------------------------------------------------------------------------
class LRUCachedItem:
    __slots__ = ('empty', 'next', 'previous', 'key', 'value')

    def __init__(self):
        self.empty    : bool            = True
        self.previous : 'LRUCachedItem' = None
        self.next     : 'LRUCachedItem' = None
        self.key      : Any             = None
        self.value    : Any             = None

# --------------------------------------------------------------------------------
# class TTLCachedItem:
#     __slots__ = ('empty', 'next', 'previous', 'key', 'value', 'timestamp')
#
#     def __init__(self):
#         self.empty    : bool            = True
#         self.previous : 'TTLCachedItem' = None
#         self.next     : 'TTLCachedItem' = None
#         self.key      : Any             = None
#         self.value    : Any             = None
#         self.timestamp: float           = 0
