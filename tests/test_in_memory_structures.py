from unittest import TestCase
from mock import (
    MagicMock,
    patch,
    mock_open
)

from collections import (
    Mapping
)
from configman.dotdict import (
    DotDict
)

from blender.in_memory_structures import (
    URLStats,
    Query,
    QueryCollection,
)


class TestURLStats(TestCase):

    def test_instantiation(self):
        config = {}
        url_stats = URLStats(config)
        self.assertTrue(url_stats.config is config)
        self.assertEqual(url_stats.number_of_repetitions, 0)

        url_stats = URLStats(config, 16)
        self.assertEqual(url_stats.number_of_repetitions, 16)

    def test_increment_count(self):
        config = {}
        url_stats = URLStats(config)
        self.assertEqual(url_stats.number_of_repetitions, 0)
        url_stats.increment_count()
        self.assertEqual(url_stats.number_of_repetitions, 1)

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStats
        a_query = Query(config)
        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 1)

        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStats
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
        url_stats1 = URLStats(config)
        url_stats1.number_of_repetitions = 17
        url_stats1.probability = 0.5

        url_stats_2 = URLStats(config)
        url_stats_2.increment_count()
        url_stats_2.probability = 0.25

        url_stats1.subsume(url_stats_2)

        self.assertEqual(url_stats1.number_of_repetitions, 18)
        self.assertEqual(url_stats_2.number_of_repetitions, 0)
        self.assertEqual(url_stats1.probability, 0.75)

    @patch('blender.in_memory_structures.laplace',)
    def test_calculate_probability_relative_to(self, laplace_mock):
        # we need control over the laplace method so that it returns a
        # known value.  Having it mocked to always return 0.0 makes it easier
        # to test the resultant values in the equations that use laplace
        laplace_mock.return_value = 0.0

        other_query_collection = MagicMock()
        other_query_collection['q1']['u1'].number_of_repetitions = 10.0
        other_query_collection.number_of_query_url_pairs = 100.0

        config = DotDict({'b': 0.0})
        stats_counter_1 = URLStats(config)
        stats_counter_1.calculate_probability_relative_to(
            other_query_collection,
            query_str='q1',
            url_str='u1'
        )
        laplace_mock.assert_called_once_with(0.0)
        self.assertEqual(stats_counter_1.probability, 0.1)

    def test_calculate_variance_relative_to(self):
        other_query_collection = MagicMock()
        other_query_collection.number_of_query_url_pairs = 100.0

        config = DotDict({'b': 1})
        stats_counter_1 = URLStats(config)
        stats_counter_1.probability = 0.1
        stats_counter_1.calculate_variance_relative_to(
            other_query_collection,
        )
        print(stats_counter_1.variance)
        self.assertAlmostEqual(stats_counter_1.variance, 0.00111111)


class TestQuery(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStats
        urls = Query(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStats
        a_query = Query(config)
        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 1)

        a_query.add('fred')

        self.assertTrue('fred' in a_query)
        self.assertEqual(a_query['fred'].number_of_repetitions, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStats
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
        config = DotDict()
        config.url_stats_class = URLStats
        a_query = Query(config)
        a_query.add('*')
        star_url = a_query['*']
        star_url.number_of_repetitions = 50
        star_url.probability = 0.5
        a_query.add('other_url')
        other_url = a_query['other_url']
        other_url.number_of_repetitions = 25
        other_url.probability = 0.25

        a_query.subsume(a_query, 'other_url')

        self.assertEqual(star_url.number_of_repetitions, 75)
        self.assertEqual(star_url.probability, 0.75)


class TestQueryCollection(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        a_query_collection = QueryCollection(config)

        self.assertTrue(a_query_collection.config is config)
        self.assertTrue(isinstance(a_query_collection.queries, Mapping))
        self.assertEqual(a_query_collection.number_of_query_url_pairs, 0)

    def test_append_star_values(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        a_query_collection = QueryCollection(config)
        a_query_collection.add(('a_query', 'a_url'))
        a_query_collection.append_star_values()

        self.assertTrue('a_query' in a_query_collection)
        self.assertTrue('a_url' in a_query_collection['a_query'])
        self.assertTrue('*' in a_query_collection['a_query'])
        self.assertEqual(a_query_collection.number_of_query_url_pairs, 1)
        self.assertEqual(a_query_collection['a_query'].number_of_urls, 1)
        self.assertEqual(a_query_collection['*'].number_of_urls, 0)

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        a_query_collection = QueryCollection(config)
        a_query_collection.add(('a_query', 'a_url'))

        self.assertTrue('a_query' in a_query_collection)
        self.assertTrue('a_url' in a_query_collection['a_query'])
        self.assertEqual(a_query_collection.number_of_query_url_pairs, 1)
        self.assertEqual(a_query_collection['a_query'].number_of_urls, 1)

        a_query_collection.add(('a_query', 'a_url'))
        self.assertTrue('a_query' in a_query_collection)
        self.assertTrue('a_url' in a_query_collection['a_query'])
        self.assertEqual(a_query_collection['a_query']['a_url'].number_of_repetitions, 2)
        self.assertEqual(a_query_collection.number_of_query_url_pairs, 2)

    def test_iter_records(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        a_query_collection = QueryCollection(config)
        a_list_of_query_url_pairs = [
            ('q1', 'u1'),
            ('q1', 'u1'),
            ('q2', 'u1'),
            ('q2', 'u2'),
            ('q3', 'u3'),
            ('q4', 'u4'),
            ('q4', 'u5'),
            ('q4', 'u4'),
        ]
        for query_url_pair in a_list_of_query_url_pairs:
            a_query_collection.add(query_url_pair)

        for i, query_url_pair in enumerate(a_list_of_query_url_pairs):
            q, u = query_url_pair
            self.assertTrue(q in a_query_collection)
            self.assertTrue(u in a_query_collection[q])

        # count of keys
        self.assertEqual(len(a_query_collection), 4)
        # count of all pairs even duplicates
        self.assertEqual(a_query_collection.number_of_query_url_pairs, 8)

        self.assertEqual(a_query_collection['q1']['u1'].number_of_repetitions, 2)
        self.assertEqual(a_query_collection['q2']['u1'].number_of_repetitions, 1)
        self.assertEqual(a_query_collection['q2']['u2'].number_of_repetitions, 1)
        self.assertEqual(a_query_collection['q3']['u3'].number_of_repetitions, 1)
        self.assertEqual(a_query_collection['q4']['u4'].number_of_repetitions, 2)
        self.assertEqual(a_query_collection['q4']['u5'].number_of_repetitions, 1)

    def test_subsume_those_not_present(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        reference_query_collection = QueryCollection(config)
        reference_list_of_query_url_pairs = [
            ('q1', 'u1'),
            ('q1', 'u1'),
            ('q2', 'u1'),
            ('q2', 'u2'),
            ('q3', 'u3'),
            ('q4', 'u4'),
            ('q4', 'u5'),
            ('q4', 'u4'),
        ]
        for query_url_pair in reference_list_of_query_url_pairs:
            reference_query_collection.add(query_url_pair)

        test_query_collection = QueryCollection(config)
        for query_url_pair in reference_list_of_query_url_pairs:
            test_query_collection.add(query_url_pair)
        additional_query_url_pairs = [
            ('q5', 'u1'),
            ('q6', 'u1'),
            ('q7', 'u1'),
            ('q8', 'u2'),
            ('q9', 'u3'),
            ('q8', 'u4'),
            ('q7', 'u5'),
            ('q4', 'u9'),
        ]
        for query_url_pair in additional_query_url_pairs:
            test_query_collection.add(query_url_pair)

        test_query_collection.subsume_those_not_present_in(reference_query_collection)

        self.assertTrue('*' in test_query_collection)
        self.assertEqual(test_query_collection['*']['*'].number_of_repetitions, 8)
        self.assertTrue('u9' not in test_query_collection['q4'])

    @patch("builtins.open", new_callable=mock_open, read_data=
        '["q1","u1"]\n'
        '["q1","u2"]\n'
        '["q2","u3"]\n'
    )
    def test_load(self, mocked_open):
        mocked_open.return_value.__iter__ = lambda self: self
        mocked_open.return_value.__next__ = lambda self: self.readline()

        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        reference_query_collection = QueryCollection(config)

        reference_query_collection.load("somefile")

        self.assertEqual(reference_query_collection.number_of_query_url_pairs, 3)
        self.assertTrue("q1" in reference_query_collection)
        self.assertTrue("u1" in reference_query_collection["q1"])
        self.assertTrue("u2" in reference_query_collection["q1"])
        self.assertEqual(reference_query_collection["q1"].number_of_urls, 2)
        self.assertTrue("q2" in reference_query_collection)
        self.assertTrue("u3" in reference_query_collection["q2"])
        self.assertEqual(reference_query_collection["q2"].number_of_urls, 1)
