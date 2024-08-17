from typing import Any, Dict

from .cached_item import CachedItem

# --------------------------------------------------------------------------------
class LRUCache:
    def __init__(self, max_size: int):
        self.max_size     : int                   = max_size
        self._cached_items: Dict[Any, CachedItem] = {}
        self.head         : CachedItem            = None
        self.__create_list()

    # --------------------------------------------------------------------------------
    def __create_list(self):
        initial_list = []
        for i in range(self.max_size):
            initial_list.append(CachedItem())

        for i in range(self.max_size):
            initial_list[i].empty = True
            if i == 0:
                initial_list[i].previous = initial_list[-1]
            else:
                initial_list[i].previous = initial_list[i-1]

            if i == self.max_size-1:
                initial_list[i].next = initial_list[0]
            else:
                initial_list[i].next = initial_list[i+1]
        self.head = initial_list[0]

    # --------------------------------------------------------------------------------
    def __list_move_to_end(self, cached_item: CachedItem, empty: bool = False):
        if self.head is cached_item:
            self.head = cached_item.next
        else:
            cached_item.previous.next = cached_item.next
            cached_item.next.previous = cached_item.previous
            cached_item.previous      = self.head.previous
            cached_item.next          = self.head
            self.head.previous.next   = cached_item
            self.head.previous        = cached_item

        if empty:
            cached_item.empty = True
            cached_item.key   = None
            cached_item.value = None

    # --------------------------------------------------------------------------------
    def __list_move_to_front(self, cached_item: CachedItem):
        if cached_item is not self.head:
            self.__list_move_to_end(cached_item, False)
            self.head = cached_item

    # --------------------------------------------------------------------------------
    def __iterator(self):
        cached_item = self.head
        for i in range(len(self._cached_items)):
            yield cached_item
            cached_item = cached_item.next

    # --------------------------------------------------------------------------------
    def clear(self):
        for cached_item in self.__iterator():
            cached_item.empty = True
            cached_item.key   = None
            cached_item.value = None
        self._cached_items.clear()

    # --------------------------------------------------------------------------------
    # does not affect cache order
    def peek(self, key: Any, default: Any = None):
        if key in self._cached_items.keys():
            return self._cached_items[key].value
        return default

    # --------------------------------------------------------------------------------
    # alters cache order
    def get(self, key: Any, default: Any = None):
        if key in self._cached_items.keys():
            return self[key]
        return default

    # --------------------------------------------------------------------------------
    # alters cache order
    def pop_item(self, key: Any, default: Any = None):
        if key in self._cached_items.keys():
            cached_item = self._cached_items.pop(key)
            value       = cached_item.value
            self.__list_move_to_end(cached_item, True)
            return value
        return default

    # --------------------------------------------------------------------------------
    # alters cache order
    def pop(self):
        if len(self._cached_items) < 1:
            return None

        cached_item       = self.head
        self.head         = cached_item.next
        return_key        = cached_item.key
        return_value      = cached_item.value
        cached_item.empty = True
        cached_item.key   = None
        cached_item.value = None
        self._cached_items.pop(return_key)
        return return_key, return_value

    # --------------------------------------------------------------------------------
    def items(self):
        for cached_item in self.__iterator():
            yield cached_item.key, cached_item.value

    # --------------------------------------------------------------------------------
    def keys(self):
        for cached_item in self.__iterator():
            yield cached_item.key

    # --------------------------------------------------------------------------------
    def values(self):
        for cached_item in self.__iterator():
            yield cached_item.value

    # --------------------------------------------------------------------------------
    def __len__(self):
        return len(self._cached_items)

    # --------------------------------------------------------------------------------
    def __contains__(self, key: Any):
        return key in self._cached_items

    # --------------------------------------------------------------------------------
    def __getitem__(self, key: Any):
        cached_item = self._cached_items[key]
        self.__list_move_to_front(cached_item)
        return cached_item.value

    # --------------------------------------------------------------------------------
    def __setitem__(self, key: Any, value: Any):
        if key in self._cached_items.keys():
            cached_item       = self._cached_items[key]
            cached_item.value = value
            self.__list_move_to_front(cached_item)
            return

        cached_item = self.head.previous

        if not cached_item.empty:
            self._cached_items.pop(cached_item.key)

        cached_item.empty       = False
        cached_item.key         = key
        cached_item.value       = value
        self._cached_items[key] = cached_item
        self.head               = cached_item

    # --------------------------------------------------------------------------------
    def __delitem__(self, key: Any):
        if key in self._cached_items.keys():
            cached_item = self._cached_items.pop(key)
            self.__list_move_to_end(cached_item, True)

    # --------------------------------------------------------------------------------
    def __iter__(self):
        for cached_item in self.__iterator():
            yield cached_item.key
