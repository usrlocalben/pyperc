"""
SortedCollection is inspired by some stackexchange bits, like

http://stackoverflow.com/questions/27672494/python-using-bisect-insort-with-key
http://code.activestate.com/recipes/577197-sortedcollection/
and, pymongo/mongoengine's interface

Usually, we only care about
    the most recent N events (with skip/limit ability for pagination)
    the next N events that come after {{some known id}}
    id search
"""

from bisect import bisect_left

class DoesNotExist(Exception):
    pass
class NotUniqueError(Exception):
    pass

class SortedCollection(object):

    def __init__(self, limit=None):
        #self.keyfunc = keyfunc
        self.keys = []
        self.data = []
        #self.limit = int(limit) if limit else None

    def insert(self, id_, item):
        #item_value = self.keyfunc(item)
        #item_value = item['id_']
        item_value = id_
        idx = bisect_left(self.keys, item_value)
        try:
            if self.keys[idx] == item_value:
                raise NotUniqueError
        except IndexError:
            pass
        self.keys.insert(idx, item_value)
        self.data.insert(idx, item)

        #if self.limit and (len(self.keys) > self.limit * 2):
        #    self.keys[:] = self.keys[-self.limit:]
        #    self.data[:] = self.data[-self.limit:]

    """
    def merge(self, items, keyfunc):
        inserted = []
        for item in items:
            id_ = keyfunc(item)
            try:
                self.insert(id_, item)
            except NotUniqueError:
                pass
            else:
                inserted.append(item)
    """

    def find_index(self, id_):
        idx = bisect_left(self.keys, id_)
        try:
            if self.keys[idx] == id_:
                return idx
            else:
                raise DoesNotExist
        except IndexError:
            raise DoesNotExist

    def find_one(self, id_, filter=None):
        idx = bisect_left(self.keys, id_)
        try:
            if self.keys[idx] == id_:
                item = self.data[idx]
                if filter:
                    return item if filter(item) else None
                else:
                    return item
            else:
                return None
        except IndexError:
            return None

    def find_gt(self, id_, skip=0, limit=None, filter=None):
        idx = bisect_left(self.keys, id_)

        try:
            if self.keys[idx] == id_:
                idx += 1
        except IndexError:
            return

        emit_count = 0
        while idx < len(self.data):
            if filter and not filter(self.data[idx]):
                pass
            else:
                if skip:
                    skip -= 1
                else:
                    if limit is not None and emit_count >= int(limit):
                        return
                    yield self.data[idx]
                    emit_count += 1
            idx += 1
                
    def find(self, skip=0, limit=None, filter=None, reverse=False):
        data = self.data
        if reverse:
            data = reversed(data)
        if filter:
            data = (item for item in data if filter(item))
        emit_count = 0
        for item in data:
            if skip:
                skip -= 1
            else:
                if limit is not None and emit_count >= int(limit):
                    return
                yield item
                emit_count += 1

