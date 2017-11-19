from unittest import TestCase
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition
)

from blender.tests.client_support import (
    local_alg
)
from blender.head_list import (
    HeadList,
    HeadListQuery,
)
from blender.in_memory_structures import (
    URLStats,
    URLStats,
    Query,
    QueryCollection
)


#class TestLocalAlg(TestCase):

    #def _create_optin_db_01(self, config):
        #q_u_db = QueryCollection(config)
        #q_u_pairs = [
            #('q1', 'q1u1', 10),
            #('q2', 'q2u1', 10),
            #('q2', 'q2u2', 20),
            #('q3', 'q3u1', 30),
            #('q4', 'q4u1', 99),
            #('q4', 'q4u2', 99),
            #('q5', 'q5u1', 10),
            #('q5', 'q5u2', 20),
            #('q6', 'q6u1', 99),
            #('q6', 'q6u2', 10),
            #('q7', 'q7u1', 99),
            #('q7', 'q7u2', 99),
        #]
        #for q, u, c in q_u_pairs:
            #for i in range(c):
                #q_u_db.add((q, u))
        #return q_u_db

    #def _create_optin_db_02(self, config):
        #q_u_db = QueryCollection(config)
        #q_u_pairs = [
            #('q1', 'q1u1', 10),
            #('q2', 'q2u1', 10),
            #('q2', 'q2u2', 20),
            #('q3', 'q3u1', 30),
            #('q4', 'q4u1', 100),
            #('q4', 'q4u2', 100),
            #('q5', 'q5u1', 10),
            #('q5', 'q5u2', 20),
            #('q6', 'q6u1', 100),
            #('q6', 'q6u2', 10),
            #('q7', 'q7u1', 100),
            #('q7', 'q7u2', 100),
            #('q8', 'q8u1', 50),
            #('q8', 'q8u2', 50),
            #('q8', 'q8u3', 50),
            #('q8', 'q8u4', 50),
            #('q8', 'q8u5', 50),
            #('q8', 'q8u6', 50),
            #('q8', 'q8u7', 45),
            #('q8', 'q8u8', 45),
        #]
        #for q, u, c in q_u_pairs:
            #for i in range(c):
                #q_u_db.add((q, u))
                #return q_u_db

    #def test_local_alg_1(self):
        #config = DotDictWithAcquisition()

        #config.epsilon = 4.0
        #config.delta = 0.000001
        #config.m_o = 10
        #config.m = 5

        #config.optin_db = DotDictWithAcquisition()
        #config.optin_db.head_list_class = QueryCollection
        #config.optin_db.url_stats_class = URLStats
        #config.optin_db.query_class = Query

        #config.head_list_db = DotDictWithAcquisition()
        #config.head_list_db.head_list_class = HeadList
        #config.head_list_db.url_stats_class = URLStats
        #config.head_list_db.query_class = Query
        #config.head_list_db.b_s = 5.0
        #config.head_list_db.tau = 83.06062179501248

        #optin_db = self._create_optin_db_01(config.optin_db)

        #head_list = create_preliminary_headlist(config.head_list_db, optin_db)



