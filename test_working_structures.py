from unittest import TestCase
from collections import (
    Mapping
)
from configman.dotdict import DotDict
from working_structures import (
    URLStatsCounter,
    URLs,
    QueryURLDatabase
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
        urls = URLs(config)
        self.assertTrue(urls.config is config)
        self.assertTrue(isinstance(urls.urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        urls = URLs(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        urls = URLs(config)
        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.touch('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 0)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)


class TestQueryURLDatabase(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        config.url_class = URLs
        q_u_db = QueryURLDatabase(config)

        self.assertTrue(q_u_db.config is config)
        self.assertTrue(isinstance(q_u_db.queries_and_urls, Mapping))

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        config.url_class = URLs
        q_u_db = QueryURLDatabase(config)
        q_u_db.add(('a_query', 'a_url'))

        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])

        q_u_db.add(('a_query', 'a_url'))
        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])
        self.assertEqual(q_u_db['a_query']['a_url'].count, 2)

    def test_iter_records(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        config.url_class = URLs
        q_u_db = QueryURLDatabase(config)
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
        self.assertEqual(i, 7)

        self.assertEqual(q_u_db['q1']['u1'].count, 2)
        self.assertEqual(q_u_db['q2']['u1'].count, 1)
        self.assertEqual(q_u_db['q2']['u2'].count, 1)
        self.assertEqual(q_u_db['q3']['u3'].count, 1)
        self.assertEqual(q_u_db['q4']['u4'].count, 2)
        self.assertEqual(q_u_db['q4']['u5'].count, 1)


    def test_add_url_star_to_all_entries(self):
        config = DotDict()
        config.url_stats_class = URLStatsCounter
        config.url_class = URLs
        q_u_db = QueryURLDatabase(config)
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

        q_u_db.add_url_star_to_all_entries()

        self.assertEqual(q_u_db['q1']['*'].count, 0)
        self.assertEqual(q_u_db['q2']['*'].count, 0)
        self.assertEqual(q_u_db['q3']['*'].count, 0)
        self.assertEqual(q_u_db['q4']['*'].count, 0)

