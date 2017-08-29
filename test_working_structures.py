from unittest import TestCase
from collections import (
    Mapping
)
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition
)
from working_structures import (
    URLStatsCounter,
    URLStatsCounterWithProbability,
    URLStatusMappingClass,
    QueryURLMappingClass,
    HeadList,
    create_preliminary_headlist,
    estimate_optin_probabilities
)


class TestURLStatsCounter(TestCase):

    def test_instantiation(self):
        config = {}
        new_stats_counter = URLStatsCounter(config)
        self.assertTrue(new_stats_counter.config is config)
        self.assertEqual(new_stats_counter.count, 0)

        new_stats_counter = URLStatsCounter(config, 16)
        self.assertEqual(new_stats_counter.count, 16)


    def test_increment_count(self):
        config = {}
        new_stats_counter = URLStatsCounter(config)
        self.assertEqual(new_stats_counter.count, 0)
        new_stats_counter.increment_count()
        self.assertEqual(new_stats_counter.count, 1)

    def test_subsume(self):
        config = {}
        stats_counter_1 = URLStatsCounter(config)
        stats_counter_1.count = 17

        stats_counter_2 = URLStatsCounter(config)
        stats_counter_2.increment_count()
        stats_counter_1.subsume(stats_counter_2)

        self.assertEqual(stats_counter_1.count, 18)
        self.assertEqual(stats_counter_2.count, 1)




class TestURLs(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        urls = URLStatusMappingClass(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        urls = URLStatusMappingClass(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        urls = URLStatusMappingClass(config)
        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)


class TestQueryURLMappingClass(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        config.url_mapping_class = URLStatusMappingClass
        q_u_db = QueryURLMappingClass(config)

        self.assertTrue(q_u_db.config is config)
        self.assertTrue(isinstance(q_u_db.queries_and_urls, Mapping))
        self.assertEqual(q_u_db.count, 0)


    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        config.url_mapping_class = URLStatusMappingClass
        q_u_db = QueryURLMappingClass(config)
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
        config.url_stats_class = URLStatsCounter
        config.url_mapping_class = URLStatusMappingClass
        q_u_db = QueryURLMappingClass(config)
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
        config.url_stats_class = URLStatsCounter
        config.url_mapping_class = URLStatusMappingClass
        reference_q_u_db = QueryURLMappingClass(config)
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

        test_q_u_db = QueryURLMappingClass(config)
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


class TestHeadList(TestCase):

    def _create_optin_db(self, config):
        q_u_db = QueryURLMappingClass(config)
        q_u_pairs = [
            ('q1', 'q1u1', 10),
            ('q2', 'q2u1', 10),
            ('q2', 'q2u2', 20),
            ('q3', 'q3u1', 30),
            ('q4', 'q4u1', 99),
            ('q4', 'q4u2', 99),
            ('q5', 'q5u1', 10),
            ('q5', 'q5u2', 20),
            ('q6', 'q6u1', 99),
            ('q6', 'q6u2', 10),
            ('q7', 'q7u1', 99),
            ('q7', 'q7u2', 99),
        ]
        for q, u, c in q_u_pairs:
            for i in range(c):
                q_u_db.add((q, u))
        return q_u_db



    def testCreation(self):
        config = DotDictWithAcquisition()

        config.opt_in_db = DotDictWithAcquisition()
        config.opt_in_db.headlist_class = QueryURLMappingClass
        config.opt_in_db.url_stats_class = URLStatsCounter
        config.opt_in_db.url_mapping_class = URLStatusMappingClass

        config.head_list_db = DotDictWithAcquisition()
        config.head_list_db.headlist_class = HeadList
        config.head_list_db.url_stats_class = URLStatsCounterWithProbability
        config.head_list_db.url_mapping_class = URLStatusMappingClass

        config.epsilon = 4.0
        config.delta = 0.000001
        config.m_o = 10
        config.m = 5

        optin_db = self._create_optin_db(config.opt_in_db)

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


