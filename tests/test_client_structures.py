from unittest import TestCase

from collections import (
    Mapping
)
from configman.dotdict import (
    DotDict
)

from blender.in_memory_structures import (
    Query,
)

from blender.client_structures import (
    ClientQuery,
    ClientURLStats
)


class TestClientUrlStats(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = ClientURLStats
        a_query = Query(config)
        self.assertTrue(a_query.config is config)
        self.assertTrue(isinstance(a_query.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = ClientURLStats
        a_query = Query(config)
        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 1)

        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = ClientURLStats
        a_query = Query(config)
        a_query.touch('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 0)

        a_query.touch('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 0)

        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 1)

    def test_subsume(self):
        config = {}
        url_stats_1 = ClientURLStats(config)
        url_stats_1.number_of_repetitions = 17
        url_stats_1.probability = 0.5

        url_stats_2 = ClientURLStats(config)
        url_stats_2.increment_count()
        url_stats_2.probability = 0.25
        url_stats_1.subsume(url_stats_2)

        self.assertEqual(url_stats_1.number_of_repetitions, 18)
        self.assertEqual(url_stats_2.number_of_repetitions, 0)
        self.assertEqual(url_stats_1.probability, 0.75)

