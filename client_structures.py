from math import (
    exp
)

from numpy.random import (
    random,
    laplace,
    choice,
)

from blender.in_memory_structures import (
    URLStatsWithProbability,
    URLStatsMapping,
    QueryURLMapping,
)


def local_alg(config, head_list, local_query_url_iter):
    """to be used in testing as in production, it will be executed by the client.  It should, therefore,
    be written in Javascript or Rust"""
    kappa = head_list.count
    tau = (
        (exp(config.epsilon_prime_q) + (config.delta_prime_q / 2.0) * (kappa - 1))
        /
        (exp(config.epsilon_prime_q) + kappa - 1)
    )
    for a_query, a_url in local_query_url_iter():
        if a_query not in head_list:
            a_query = '*'
        if a_url not in head_list[a_query]:
            a_url = '*'

        if random() <= (1 - tau):
            # there is confusion on the significance of a database structure has only unqiue <q, u> pairs
            # or duplicates.  Some code clearly allows duplicates.  the definiton of |D| is for unique or
            # with duplicates?
            a_query = choice(head_list.keys())

# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes

class URLStatsForClient(URLStatsWithProbability):
    def __init__(self, config, count=0):
        super(URLStatsForClient, self).__init__(config, count)
        self.probability = 0.0  # the computed probability of this URL
        self.variance = 0.0  # the variance of this URL

    def calculate_probability_relative_to(self, other_query_url_mapping, query='*', url='*', r_c_q_u=0.0, head_list=None):
        other_query = other_query_url_mapping[query]
        other_url = other_query[url]
        head_list_query = head_list[query]
        # from Figure 5, line 16
        # broken down into separate steps to help clarity
        term_1 = r_c_q_u
        term_2 = (1.0 - other_query.tau) * head_list.tau * other_query.probability / (head_list_query.count - 1)
        term_3 = (1.0 - other_query.tau) * (1.0 - other_query.probability) / ((head_list. count - 1) * head_list_query.count)
        term_4 = head_list.tau * (head_list_query.tau - ((1 - head_list_query.tau) / (head_list_query.count - 1)))
        self.probability = (term_1 - term_2 - term_3) / term_4


    def calculate_variance_relative_to(self, other_query_url_mapping, query='*', url='*', r_c_q_u=0.0, head_list=None):
        other_query = other_query_url_mapping[query]
        other_url = other_query[url]
        head_list_query = head_list[query]
        # from Figure 5, line 17
        # broken down into separate steps to help clarity
        term_1 = r_c_q_u * (1.0 - r_c_q_u) / (other_query_url_mapping.count - 1.0)
        term_2a = 2.0 * other_query_url_mapping.count / (other_query_url_mapping.count - 1.0)
        # note t1 / t2 / t3 here instead of the equivalent t1 / (t2 * t3)
        term_2b = (1.0 - head_list.tau) / (head_list.count - 1.0) / head_list_query.count
        term_2c = (head_list.tau - head_list.tau * head_list_query.tau) / (head_list_query.count - 1.0)
        term_2d = r_c_q_u * (head_list.count - 2.0 + head_list.tau) / (head_list.count * head_list.tau - 1.0)
        term2 = term_2a * (term_2b - term_2c) * term_2d
        # note t1 / t2 / t3 here instead of the equivalent t1 / (t2 * t3)
        term3a = (1.0 - head_list.tau) / (head_list.count - 1.0) / head_list_query.count
        term3b = pow((head_list.tau - head_list.tau * head_list_query.tau) / (head_list_query.count - 1.0), 2)
        term3 = (term3a - term3b) * other_query.variance
        term4 = 1.0 / pow(head_list.tau, 2) / pow(head_list_query.tau - ((1.0 - head_list_query.tau)/(head_list_query.count - 1.0)), 2)
        self.variance = (term1 + term2 + term3) * term4


# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value

class URLStatsMappingForClient(URLStatsMapping):
    def __init__(self, config):
        super(URLStatsMappingForClient, self).__init__(config)
        self.probability = 0.0  # TODO
        self.variance = 0.0  # TODO

    def calculate_probabilities_relative_to(self, other_query_url_mapping, head_list):
        # from Figure 5, line 10
        for query in head_list.keys():
            # from Figure 5, line 11
            # this is very ambiguous: "the fraction of queries q in D_c"
            # does it mean that <q1, u1>, <q1, u2> is counted as two queries
            # or only one?
            fraction_of_this_query_in_other_mapping = (
                other_query_url_mapping[query].count / other_query_url_mapping.count
            )
            ratio = (1.0 - head_list.tau) / (head_list.count - 1.0)
            # from Figure 5, line 12
            self.probability = (
                (fraction_of_this_query_in_other_mapping - ratio)
                /
                (head_list.tau - ratio)
            )
            # from Figure 5, line 13
            self.variance = (
                (1.0 / pow(head_list.tau - ratio, 2))
                *
                (fraction_of_this_query_in_other_mapping * (1 - fraction_of_this_query_in_other_mapping))
                /
                (other_query_url_mapping.count - 1)
            )

            # from Figure 5, line 14
            for url in head_list[query]:
                # Figure 5, line 15
                r_c_q_u = other_url.count / other_query_url_mapping.count  # TODO: rename
                # Figure 5, line 16 implemented in the
                self[query][url].calculate_probability_relative_to(
                    other_query_url_mapping,
                    query=query,
                    url=url,
                    r_c_q_u=r_c_q_u,
                    head_list=None
                )
                self[query][url].calculate_variance_relative_to(
                    other_query_url_mapping,
                    query=query,
                    url=url,
                    r_c_q_u=r_c_q_u,
                    head_list=None
                )


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value

class QueryUrlMappingForClient(QueryURLMapping):
    pass
