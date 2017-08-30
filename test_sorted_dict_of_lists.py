from unittest import TestCase

from sorted_dict_of_lists import (
    SortedDictOfLists
)


class TestSortedDictOfLists(TestCase):

    def test_instantiation(self):
        sd = SortedDictOfLists()

        self.assertEqual(len(sd), 0)

    def test_setitem(self):
        sd = SortedDictOfLists()

        sd['a'].append(15)
        self.assertEqual(sd['a'], [15])
        self.assertEqual(len(sd), 1)



