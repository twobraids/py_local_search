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

    def test_iter_records(self):
        sd = SortedDictOfLists()
        sd['n'].append(33)
        sd['o'].append(44)
        sd['b'].append(32)
        sd['z'].append(88)

        sd['b'].append(19)
        sd['o'].append(22)

        self.assertEqual(list(sd.keys()), ['b', 'n', 'o', 'z'])
        self.assertEqual(
            list(sd.iter_records()),
            [('z', 88), ('o', 44), ('o', 22), ('n', 33), ('b', 32), ('b', 19)]
        )





