
class OrderedDict(dict):
    def __init__(self, items=None):
        self._keys = []
        if not items:
            return
        if isinstance(items, dict):
            raise TypeError('Can only assign a list to OrderedDict')
        for key, value in items:
            self[key] = value

    @classmethod
    def fromkeys(cls, keys, value=None):
        return cls((x, value) for x in keys)

    def __setitem__(self, key, value):
        if key not in self:
            self._keys.append(key)
        dict.__setitem__(self, key, value)

    def copy(self):
        return self.__class__(self.items())
    
    def pop(self, key):
        value = dict.pop(self, key)
        self._keys.remove(key)
        return value

    def __delitem__(self, key):
        self.pop(key)

    def __iter__(self):
        for key in self._keys:
            yield key

    def iterkeys(self):
        return iter(self)

    def keys(self):
        return list(self)

    def values(self):
        return list(self.itervalues())

    def items(self):
        return list(self.iteritems())

    def itervalues(self):
        for key in self._keys:
            yield self[key]

    def iteritems(self):
        for key in self._keys:
            yield key, self[key]
