from unittest import TestCase
from mock import (
    MagicMock,
    patch
)

from collections import (
    Mapping
)
from configman.dotdict import (
    DotDict
)

from blender.in_memory_structures import (
    URLCounter,
    URLStatsWithProbability,
    URLStatsMapping,
    QueryURLMapping,
)


class TestURLCounter(TestCase):

    def test_instantiation(self):
        config = {}
        new_stats_counter = URLCounter(config)
        self.assertTrue(new_stats_counter.config is config)
        self.assertEqual(new_stats_counter.count, 0)

        new_stats_counter = URLCounter(config, 16)
        self.assertEqual(new_stats_counter.count, 16)

    def test_increment_count(self):
        config = {}
        new_stats_counter = URLCounter(config)
        self.assertEqual(new_stats_counter.count, 0)
        new_stats_counter.increment_count()
        self.assertEqual(new_stats_counter.count, 1)

    def test_subsume(self):
        config = {}
        stats_counter_1 = URLCounter(config)
        stats_counter_1.count = 17
        stats_counter_1.probability = 0.5

        stats_counter_2 = URLCounter(config)
        stats_counter_2.increment_count()
        stats_counter_1.subsume(stats_counter_2)

        self.assertEqual(stats_counter_1.count, 18)
        self.assertEqual(stats_counter_2.count, 1)


class TestURLStats(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        urls = URLStatsMapping(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        urls = URLStatsMapping(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        urls = URLStatsMapping(config)
        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)


class TestURLStatsWithProbabity(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStatsWithProbability
        urls = URLStatsMapping(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStatsWithProbability
        urls = URLStatsMapping(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStatsWithProbability
        urls = URLStatsMapping(config)
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
        stats_counter_1 = URLStatsWithProbability(config)
        stats_counter_1.count = 17
        stats_counter_1.probability = 0.5

        stats_counter_2 = URLStatsWithProbability(config)
        stats_counter_2.increment_count()
        stats_counter_2.probability = 0.25
        stats_counter_1.subsume(stats_counter_2)

        self.assertEqual(stats_counter_1.count, 18)
        self.assertEqual(stats_counter_2.count, 1)
        self.assertEqual(stats_counter_1.probability, 0.75)

    @patch('blender.in_memory_structures.laplace',)
    def test_calculate_probability_relative_to(self, laplace_mock):
        # we need control over the laplace method so that it returns a
        # known value.  Having it mocked to always return 1 makes it easier
        # to test the resultant values in the equations that use laplace
        laplace_mock.return_value = 1

        other_query_url_mapping = MagicMock()
        other_query_url_mapping['q1']['u1'].count = 10.0
        other_query_url_mapping.count = 100.0

        config = {}
        stats_counter_1 = URLStatsWithProbability(config)
        stats_counter_1.calculate_probability_relative_to(
            other_query_url_mapping,
            query='q1',
            url='u1'
        )
        laplace_mock.assert_called_once_with(0.0)
        self.assertEqual(stats_counter_1.probability, 0.1)

    def test_calculate_variance_relative_to(self):
        other_query_url_mapping = MagicMock()
        other_query_url_mapping.count = 100.0

        config = {}
        stats_counter_1 = URLStatsWithProbability(config)
        stats_counter_1.probability = 0.1
        stats_counter_1.calculate_variance_relative_to(
            other_query_url_mapping,
            b_t=1.0
        )
        print(stats_counter_1.variance)
        self.assertAlmostEqual(stats_counter_1.variance, 0.00111111)



class TestQueryURLMappingClass(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        config.url_mapping_class = URLStatsMapping
        q_u_db = QueryURLMapping(config)

        self.assertTrue(q_u_db.config is config)
        self.assertTrue(isinstance(q_u_db.queries_and_urls, Mapping))
        self.assertEqual(q_u_db.count, 0)

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        config.url_mapping_class = URLStatsMapping
        q_u_db = QueryURLMapping(config)
        q_u_db.add(('a_query', 'a_url'))

        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])
        self.assertEqual(q_u_db.count, 1)

        q_u_db.add(('a_query', 'a_url'))
        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])
        self.assertEqual(q_u_db['a_query']['a_url'].count, 2)
        self.assertEqual(q_u_db.count, 2)

    def test_iter_records(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        config.url_mapping_class = URLStatsMapping
        q_u_db = QueryURLMapping(config)
        q_u_pairs = [
            ('q1', 'u1'),
            ('q1', 'u1'),
            ('q2', 'u1'),
            ('q2', 'u2'),
            ('q3', 'u3'),
            ('q4', 'u4'),
            ('q4', 'u5'),
            ('q4', 'u4'),
        ]
        for q_u in q_u_pairs:
            q_u_db.add(q_u)

        for i, q_u in enumerate(q_u_pairs):
            q, u = q_u
            self.assertTrue(q in q_u_db)
            self.assertTrue(u in q_u_db[q])

        # count of keys
        self.assertEqual(len(q_u_db), 4)
        # count of all pairs even duplicates
        self.assertEqual(q_u_db.count, 8)

        self.assertEqual(q_u_db['q1']['u1'].count, 2)
        self.assertEqual(q_u_db['q2']['u1'].count, 1)
        self.assertEqual(q_u_db['q2']['u2'].count, 1)
        self.assertEqual(q_u_db['q3']['u3'].count, 1)
        self.assertEqual(q_u_db['q4']['u4'].count, 2)
        self.assertEqual(q_u_db['q4']['u5'].count, 1)

    def test_subsume_those_not_present(self):
        config = DotDict()
        config.url_stats_class = URLCounter
        config.url_mapping_class = URLStatsMapping
        reference_q_u_db = QueryURLMapping(config)
        q_u_pairs = [
            ('q1', 'u1'),
            ('q1', 'u1'),
            ('q2', 'u1'),
            ('q2', 'u2'),
            ('q3', 'u3'),
            ('q4', 'u4'),
            ('q4', 'u5'),
            ('q4', 'u4'),
        ]
        for q_u in q_u_pairs:
            reference_q_u_db.add(q_u)

        test_q_u_db = QueryURLMapping(config)
        for q_u in q_u_pairs:
            test_q_u_db.add(q_u)
        additional_q_u_pairs = [
            ('q5', 'u1'),
            ('q6', 'u1'),
            ('q7', 'u1'),
            ('q8', 'u2'),
            ('q9', 'u3'),
            ('q8', 'u4'),
            ('q7', 'u5'),
            ('q4', 'u9'),
        ]
        for q_u in additional_q_u_pairs:
            test_q_u_db.add(q_u)

        test_q_u_db.subsume_those_not_present_in(reference_q_u_db)

        self.assertTrue('*' in test_q_u_db)
        self.assertEqual(test_q_u_db['*']['*'].count, 8)
        self.assertTrue('u9' not in test_q_u_db['q4'])
