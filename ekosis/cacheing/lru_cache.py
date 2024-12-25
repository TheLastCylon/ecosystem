from typing import Any, Dict

from .cached_item import LRUCachedItem

# --------------------------------------------------------------------------------
class LRUCache:
    def __init__(self, max_size: int):
        self.max_size     : int                   = max_size
        self._cached_items: Dict[Any, LRUCachedItem] = {}
        self.head         : LRUCachedItem            = None
        self.tail         : LRUCachedItem            = None

    # --------------------------------------------------------------------------------
    def __insert(self, key: Any, value: Any):
        new_node       = LRUCachedItem()
        new_node.empty = False
        new_node.key   = key
        new_node.value = value
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.previous = self.tail
            new_node.next     = self.head
            if self.tail is self.head:
                self.head.previous = new_node
                self.head.next     = new_node
            else:
                self.tail.next     = new_node
                self.head.previous = new_node
        self._cached_items[key] = new_node
        return new_node

    # --------------------------------------------------------------------------------
    def __replace_least_recently_used(self, key: Any, value: Any):
        existing_node = self.head.previous

        if not existing_node.empty:
            self._cached_items.pop(existing_node.key)

        existing_node.empty     = False
        existing_node.key       = key
        existing_node.value     = value
        self._cached_items[key] = existing_node
        self.head               = existing_node

    # --------------------------------------------------------------------------------
    def __list_move_to_end(self, cached_item: LRUCachedItem, empty: bool = False):
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
    def __list_move_to_front(self, cached_item: LRUCachedItem):
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

        if len(self._cached_items) < self.max_size:
            cached_item = self.__insert(key, value)
            self.head   = cached_item
        else:
            self.__replace_least_recently_used(key, value)

    # --------------------------------------------------------------------------------
    def __delitem__(self, key: Any):
        if key in self._cached_items.keys():
            cached_item = self._cached_items.pop(key)
            self.__list_move_to_end(cached_item, True)

    # --------------------------------------------------------------------------------
    def __iter__(self):
        for cached_item in self.__iterator():
            yield cached_item.key
