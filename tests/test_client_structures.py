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

        curls = ClientURLStats(config)
        self.assertEqual(curls.config, config)
        self.assertEqual(curls.number_of_repetitions, 0)
        self.assertEqual(curls.probability, 0.0)
        self.assertEqual(curls.variance, 0.0)

    def test_calculate_probability_relative_to(self):
        pass
