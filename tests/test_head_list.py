from unittest import TestCase
from mock import (
    MagicMock,
    patch
)
from collections import (
    Mapping
)
from configman import (
    configuration,
)
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition
)

from blender.head_list import (
    HeadList,
    HeadListURLStatsMapping,
)
from blender.in_memory_structures import (
    URLCounter,
    URLStatsWithProbability,
    URLStatsMapping,
    QueryURLMapping
)
from blender.main import (
    required_config,
    default_data_structures,
    create_preliminary_headlist,
    estimate_optin_probabilities
)

from blender.tests.synthetic_data import (
    standard_constants,
    load_tiny_data,
    load_small_data
)


class TestHeadListURLStatsMapping(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLCounter

        urls = HeadListURLStatsMapping(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))
        self.assertEqual(urls.tau, 0.0)

    def test_calculate_tau(self):
        config = DotDict()
        config.epsilon_prime_q = 1.0
        config.delta_prime_q = 1.0
        config.epsilon_prime_u = 1.0
        config.url_stats_class = URLCounter

        urls = HeadListURLStatsMapping(config)
        urls.add('u1')
        urls.add('u2')
        urls.calculate_tau()

        self.assertEqual(urls.count, 2.0)
        print(urls.tau)
        self.assertAlmostEqual(urls.tau, 0.865529289)


class TestHeadList(TestCase):
    def test_creation(self):
        config = configuration(
            definition_source=required_config,
            values_source_list=[
                default_data_structures,
                standard_constants,
            ]
        )

        self.assertEqual(config.head_list_db.b_s, 5.0)
        self.assertEqual(config.head_list_db.tau, 83.06062179501248)
        self.assertEqual(config.head_list_db.head_list_class, HeadList)
        self.assertEqual(config.optin_db.optin_db_class, QueryURLMapping)

        q_u_db = config.optin_db.optin_db_class(config.optin_db)

        optin_db = load_tiny_data(q_u_db)

        head_list = create_preliminary_headlist(config.head_list_db, optin_db)

        self.assertEqual(len(head_list), 4)
        self.assertEqual(len(list(head_list.iter_records())), 6)
        self.assertTrue('*' in head_list)
        self.assertTrue('q4' in head_list)
        self.assertTrue('q1' not in head_list)
        self.assertTrue('q2' not in head_list)
        self.assertTrue('q3' not in head_list)
        self.assertTrue('q5' not in head_list)
        self.assertTrue('q6' in head_list)
        self.assertTrue('q7' in head_list)
        self.assertTrue('q4u1' in head_list['q4'])
        self.assertTrue('q4u2' in head_list['q4'])
        self.assertTrue('q6u1' in head_list['q6'])
        self.assertTrue('q6u2' not in head_list['q6'])
        self.assertTrue('q7u1' in head_list['q7'])
        self.assertTrue('q7u2' in head_list['q7'])

    @patch('blender.in_memory_structures.laplace',)
    def test_calculate_probabilities_relative_to(self, laplace_mock):

        # we need control over the laplace method so that it returns a
        # known value.  Having it mocked to always return 1 makes it easier
        # to test the resultant values in the equations that use laplace
        laplace_mock.return_value = 1

        config = configuration(
            definition_source=required_config,
            values_source_list=[
                default_data_structures,
                standard_constants,
            ]
        )

        optin_db = load_small_data(
            config.optin_db.optin_db_class(config.optin_db)
        )
        head_list = create_preliminary_headlist(config.head_list_db, optin_db)

        optin_db.subsume_those_not_present_in(head_list)

        for query, url in optin_db.iter_records():
            url_stats = optin_db[query][url]
            if query == '*':
                self.assertEqual(url_stats.count, 500)
            else:
                self.assertEqual(url_stats.count, 100)

        head_list.calculate_probabilities_relative_to(optin_db)

        for query, url in optin_db.iter_records():
            url_stats = head_list[query][url]
            if query == '*':
                self.assertEqual(url_stats.probability, 0.5)
            else:
                self.assertEqual(url_stats.probability, 0.1)

    @patch('blender.in_memory_structures.laplace',)
    def test_subsume_entries_beyond_max_size(self, laplace_mock):
        # we need control over the laplace method so that it returns a
        # known value.  Having it mocked to always return 1 makes it easier
        # to test the resultant values in the equations that use laplace
        laplace_mock.return_value = 1

        constants_overridden = {
            "head_list_db.m": 2,
        }

        config = configuration(
            definition_source=required_config,
            values_source_list=[
                default_data_structures,
                standard_constants,
                constants_overridden,
            ]
        )

        optin_db = load_small_data(
            config.optin_db.optin_db_class(config.optin_db)
        )
        head_list = create_preliminary_headlist(config.head_list_db, optin_db)
        self.assertTrue('*' in head_list)
        self.assertTrue('*' not in optin_db)
        optin_db.subsume_those_not_present_in(head_list)
        self.assertTrue('*' in optin_db)
        self.assertEqual(optin_db['*']['*'].count, 500)
        self.assertEqual(head_list['*']['*'].count, 0)
        self.assertEqual(head_list['*'].probability, 0.0)

        head_list.calculate_probabilities_relative_to(optin_db)
        self.assertEqual(optin_db['*']['*'].count, 500)
        self.assertEqual(head_list['*']['*'].count, 0)
        self.assertEqual(head_list['*'].probability, 0.5)

        head_list.subsume_entries_beyond_max_size()
        self.assertEqual(optin_db['*']['*'].count, 500)
        self.assertEqual(head_list['*']['*'].count, 1)
        self.assertEqual(head_list['*'].probability, 0.6)

        # why 5 if m is 2?
        #     m selects the number of queries not the number of <q, u> pairs.
        #     2 queries were selected and they each had 2 urls for a total of 4
        #     1 query was rejected and it had 1 url
        #     the <*, *> had a count of 0 to start so the one rejected query
        #         was added to make the total 1
        #     with 1 in <*, *> and 4 in the selected list, the final total is 5
        self.assertEqual(head_list.count, 5)

        self.assertTrue('q1' not in head_list)
        self.assertTrue('q2' not in head_list)
        self.assertTrue('q3' not in head_list)
        self.assertTrue('q4' in head_list)
        self.assertTrue('q4u1' in head_list['q4'])
        self.assertTrue('q4u2' in head_list['q4'])
        self.assertTrue('q5' not in head_list)
        self.assertTrue('q6' not in head_list)
        self.assertTrue('q7' in head_list)
        self.assertTrue('q7u1' in head_list['q7'])
        self.assertTrue('q7u2' in head_list['q7'])

        # ensure that the sum of all probabilities in the head_list
        # is extremely close to 1.0  (summing floats is frequently imprecise)
        sum = 0.0
        for query in head_list.keys():
            sum += head_list[query].probability
        self.assertAlmostEqual(sum, 1.0)

    @patch('blender.in_memory_structures.laplace',)
    def test_calculate_sigma_relative_to(self, laplace_mock):

        # we need control over the laplace method so that it returns a
        # known value.  Having it mocked to always return 1 makes it easier
        # to test the resultant values in the equations that use laplace
        laplace_mock.return_value = 1

        constants_overridden = {
            "head_list_db.m": 2,
        }

        config = configuration(
            definition_source=required_config,
            values_source_list=[
                default_data_structures,
                standard_constants,
                constants_overridden,
            ]
        )

        optin_db = load_small_data(
            config.optin_db.optin_db_class(config.optin_db)
        )
        head_list = create_preliminary_headlist(config.head_list_db, optin_db)
        optin_db.subsume_those_not_present_in(head_list)
        head_list.calculate_probabilities_relative_to(optin_db)
        head_list.subsume_entries_beyond_max_size()

        head_list.calculate_variance_relative_to(optin_db)

        for query, url in head_list.iter_records():
            url_stats = head_list[query][url]
            # TODO: how do we determine that these values are correct?
            print(query, url, url_stats.count, url_stats.probability, url_stats.variance)
