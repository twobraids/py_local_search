from unittest import TestCase
from mock import (
    Mock,
    MagicMock
)

from collections import (
    Mapping,
    defaultdict
)
from configman.dotdict import (
    DotDict
)

from blender.in_memory_structures import (
    Query,
)

from blender.client_structures import (
    ClientQuery,
    ClientURLStats,
    ClientQueryCollection
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
        # TODO: is it even possible to make reasonable test case?
        config = DotDict()
        config.url_stats_class = ClientURLStats

        mocked_query = Mock()
        mocked_query.tau = 0.5
        mocked_query.probability = 0.5
        mocked_other_query_url_mapping = DotDict()
        mocked_other_query_url_mapping['some_query'] = mocked_query

        mocked_head_list_query = Mock()
        mocked_head_list_query.tau = 0.5
        mocked_head_list_query.probability = 0.5
        mocked_head_list_query.number_of_unique_urls = 3

        mocked_head_list = DotDict()
        mocked_head_list['some_query'] = mocked_head_list_query
        mocked_head_list.tau = 1.0
        mocked_head_list.number_of_queries = 101

        stats = ClientURLStats(config)
        stats.calculate_probability_relative_to(
            mocked_other_query_url_mapping,
            query_str='some_query',
            head_list=mocked_head_list,
            r_c_q_u=0.0
        )

        self.assertAlmostEqual(stats.probability, -0.5033333333333333)  # negative, really?

    def test_calculate_variance_relative_to(self):
        # TODO: is it even possible to make reasonable test case?
        config = DotDict()
        config.url_stats_class = ClientURLStats

        mocked_query = Mock()
        mocked_query.tau = 0.5
        mocked_query.probability = 0.5
        mocked_query.variance = 1.0
        mocked_other_query_url_mapping = DotDict()
        mocked_other_query_url_mapping['some_query'] = mocked_query
        mocked_other_query_url_mapping.number_of_query_url_pairs = 1001

        mocked_head_list_query = Mock()
        mocked_head_list_query.tau = 0.5
        mocked_head_list_query.probability = 0.5
        mocked_head_list_query.number_of_unique_urls = 3

        mocked_head_list = DotDict()
        mocked_head_list['some_query'] = mocked_head_list_query
        mocked_head_list.tau = 1.0
        mocked_head_list.number_of_queries = 101

        stats = ClientURLStats(config)
        stats.calculate_variance_relative_to(
            mocked_other_query_url_mapping,
            query_str='some_query',
            head_list=mocked_head_list,
            r_c_q_u=0.0
        )

        self.assertAlmostEqual(stats.probability, 0.0)


class TestClientQuery(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = ClientURLStats

        query = ClientQuery(config)

        self.assertEqual(query.config, config)
        self.assertEqual(query.probability, 0.0)
        self.assertEqual(query.variance, 0.0)
        self.assertEqual(query.number_of_urls, 0)

        query.add('some_url')

        self.assertTrue(isinstance(query.urls, defaultdict))
        self.assertTrue(isinstance(query['some_url'], ClientURLStats))
        self.assertEqual(query['some_url'].number_of_repetitions, 1)
        self.assertEqual(query.number_of_urls, 1)
        self.assertEqual(query.number_of_unique_urls, 1)

        query.add('some_url')
        self.assertEqual(query.number_of_urls, 2)
        self.assertEqual(query.number_of_unique_urls, 1)

    def test_calculate_probabilities_relative_to(self):
        config = DotDict()
        config.url_stats_class = ClientURLStats

        query = ClientQuery(config)

        # TODO: I have no idea how to reasonably test this

class TestClientQueryCollection(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = ClientURLStats
        config.query_class = ClientQuery

        client_query_collection = ClientQueryCollection(config)

        self.assertEqual(client_query_collection.number_of_query_url_pairs, 0)

        client_query_collection.add(('some_query', 'some_url'))

        self.assertTrue(isinstance(client_query_collection.queries, defaultdict))
        self.assertEqual(client_query_collection.number_of_queries, 1)
        self.assertEqual(client_query_collection.number_of_query_url_pairs, 1)

        client_query_collection.add(('some_query', 'some_other_url'))

        self.assertEqual(client_query_collection.number_of_queries, 1)
        self.assertEqual(client_query_collection.number_of_query_url_pairs, 2)

        client_query_collection.add(('some_other_query', 'some_other_url'))
        self.assertEqual(client_query_collection.number_of_queries, 2)
        self.assertEqual(client_query_collection.number_of_query_url_pairs, 3)
