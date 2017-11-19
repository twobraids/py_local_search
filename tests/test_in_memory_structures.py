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
    URLStats,
    Query,
    QueryCollection,
)


class TestURLStats(TestCase):

    def test_instantiation(self):
        config = {}
        new_stats_counter = URLStats(config)
        self.assertTrue(new_stats_counter.config is config)
        self.assertEqual(new_stats_counter.count, 0)

        new_stats_counter = URLStats(config, 16)
        self.assertEqual(new_stats_counter.count, 16)

    def test_increment_count(self):
        config = {}
        new_stats_counter = URLStats(config)
        self.assertEqual(new_stats_counter.count, 0)
        new_stats_counter.increment_count()
        self.assertEqual(new_stats_counter.count, 1)

    def test_subsume(self):
        config = {}
        url_stats1 = URLStats(config)
        url_stats1.count = 17

        url_stats_2 = URLStats(config)
        url_stats_2.increment_count()
        url_stats1.subsume(url_stats_2)

        self.assertEqual(url_stats1.count, 18)
        self.assertEqual(url_stats_2.count, 1)

    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStats
        urls = Query(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStats
        urls = Query(config)
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
        url_stats1 = URLStats(config)
        url_stats1.count = 17
        url_stats1.probability = 0.5

        url_stats_2 = URLStats(config)
        url_stats_2.increment_count()
        url_stats_2.probability = 0.25

        url_stats1.subsume(url_stats_2)

        self.assertEqual(url_stats1.count, 18)
        self.assertEqual(url_stats_2.count, 0)
        self.assertEqual(url_stats1.probability, 0.75)

    @patch('blender.in_memory_structures.laplace',)
    def test_calculate_probability_relative_to(self, laplace_mock):
        # we need control over the laplace method so that it returns a
        # known value.  Having it mocked to always return 0.0 makes it easier
        # to test the resultant values in the equations that use laplace
        laplace_mock.return_value = 0.0

        other_url_url_mapping = MagicMock()
        other_url_url_mapping['q1']['u1'].count = 10.0
        other_url_url_mapping.count = 100.0

        config = {}
        stats_counter_1 = URLStats(config)
        stats_counter_1.calculate_probability_relative_to(
            other_url_url_mapping,
            query_str='q1',
            url_str='u1'
        )
        laplace_mock.assert_called_once_with(0.0)
        self.assertEqual(stats_counter_1.probability, 0.1)

    def test_calculate_variance_relative_to(self):
        other_url_url_mapping = MagicMock()
        other_url_url_mapping.count = 100.0

        config = {}
        stats_counter_1 = URLStats(config)
        stats_counter_1.probability = 0.1
        stats_counter_1.calculate_variance_relative_to(
            other_url_url_mapping,
            b_t=1.0
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
        urls = Query(config)
        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 1)

        urls.add('fred')

        self.assertTrue('fred' in urls)
        self.assertEqual(urls['fred'].count, 2)

    def test_touch(self):
        config = DotDict()
        config.url_stats_class = URLStats
        urls = Query(config)
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
        config = DotDict()
        config.url_stats_class = URLStats
        a_query = Query(config)
        a_query.add('*')
        star_url = a_query['*']
        star_url.count = 50
        star_url.probability = 0.5
        a_query.add('other_url')
        other_url = a_query['other_url']
        other_url.count = 25
        other_url.probability = 0.25

        a_query.subsume(a_query, 'other_url')

        self.assertEqual(star_url.count, 75)
        self.assertEqual(star_url.probability, 0.75)


class TestQueryCollection(TestCase):

    def test_instantiation(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        q_u_db = QueryCollection(config)

        self.assertTrue(q_u_db.config is config)
        self.assertTrue(isinstance(q_u_db.queries, Mapping))
        self.assertEqual(q_u_db.count, 0)

    def test_append_star_values(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        q_u_db = QueryCollection(config)
        q_u_db.add(('a_query', 'a_url'))
        q_u_db.append_star_values()

        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])
        self.assertTrue('*' in q_u_db['a_query'])
        self.assertEqual(q_u_db.count, 1)
        self.assertEqual(q_u_db['a_query'].count, 1)
        self.assertEqual(q_u_db['*'].count, 0)


    def test_add(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        q_u_db = QueryCollection(config)
        q_u_db.add(('a_query', 'a_url'))

        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])
        self.assertEqual(q_u_db.count, 1)
        self.assertEqual(q_u_db['a_query'].count, 1)

        q_u_db.add(('a_query', 'a_url'))
        self.assertTrue('a_query' in q_u_db)
        self.assertTrue('a_url' in q_u_db['a_query'])
        self.assertEqual(q_u_db['a_query']['a_url'].count, 2)
        self.assertEqual(q_u_db.count, 2)

    def test_iter_records(self):
        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        q_u_db = QueryCollection(config)
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
        config.url_stats_class = URLStats
        config.query_class = Query
        reference_q_u_db = QueryCollection(config)
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

        test_q_u_db = QueryCollection(config)
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

    @patch("builtins.open", new_callable=mock_open, read_data=
        '["q1","u1"]\n'
        '["q1","u2"]\n'
        '["q2","u3"]\n'
    )
    def test_load(self, mocked_open):
        mocked_open.return_value.__iter__ = lambda self:self
        mocked_open.return_value.__next__ = lambda self: self.readline()

        config = DotDict()
        config.url_stats_class = URLStats
        config.query_class = Query
        reference_q_u_db = QueryCollection(config)

        reference_q_u_db.load("somefile")

        self.assertEqual(reference_q_u_db.count, 3)
        self.assertTrue("q1" in reference_q_u_db)
        self.assertTrue("u1" in reference_q_u_db["q1"])
        self.assertTrue("u2" in reference_q_u_db["q1"])
        self.assertEqual(reference_q_u_db["q1"].count, 2)
        self.assertTrue("q2" in reference_q_u_db)
        self.assertTrue("u3" in reference_q_u_db["q2"])
        self.assertEqual(reference_q_u_db["q2"].count, 1)

