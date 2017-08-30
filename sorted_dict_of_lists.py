from sortedcontainers import (
    SortedDict,
)

class SortedDictOfLists(SortedDict):

    def __getitem__(self, key):
        try:
            return super(SortedDictOfLists, self).__getitem__(key)
        except KeyError:
            self[key] = []
            return self[key]

    def iter_records(self):
        for key in reversed(self.keys()):
            for value in self[key]:
                yield key, value
