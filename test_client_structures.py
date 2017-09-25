from unittest import TestCase

from collections import (
    Mapping
)
from configman.dotdict import (
    DotDict
)

from blender.in_memory_structures import (
    URLCounter,
    URLStatsMappingClass,
    QueryURLMappingClass,
)

from blender.optin_structures import (
    URLStatsForOptin,
)



class TestURLStatsForOptin(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStatsForOptin
        urls = URLStatsMappingClass(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStatsForOptin
        urls = URLStatsMappingClass(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStatsForOptin
        urls = URLStatsMappingClass(config)
        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

    def test_subsume(self):
        config = {}
        stats_counter_1 = URLStatsForOptin(config)
        stats_counter_1.count = 17
        stats_counter_1.probability = 0.5

        stats_counter_2 = URLStatsForOptin(config)
        stats_counter_2.increment_count()
        stats_counter_2.probability = 0.25
        stats_counter_1.subsume(stats_counter_2)

        self.assertEqual(stats_counter_1.count, 18)
        self.assertEqual(stats_counter_2.count, 1)
        self.assertEqual(stats_counter_1.probability, 0.75)

