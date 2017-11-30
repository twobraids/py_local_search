from blender.in_memory_structures import (
    URLStats,
    Query,
    QueryCollection,
)


# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes
class ClientURLStats(URLStats):
    def __init__(self, config, count=0):
        super(ClientURLStats, self).__init__(config, count)

    def calculate_probability_relative_to(self, other_query_url_mapping, query_str='*', url_str='*', r_c_q_u=0.0, head_list=None):
        other_query = other_query_url_mapping[query_str]
        head_list_query = head_list[query_str]
        # from Figure 5, line 16
        # broken down into separate steps to help clarity
        term_1 = r_c_q_u
        term_2 = (1.0 - other_query.tau) * head_list.tau * other_query.probability / (head_list_query.kappa_q - 1)
        term_3 = (1.0 - other_query.tau) * (1.0 - other_query.probability) / ((head_list.number_of_query_url_pairs - 1) * head_list_query.kappa_q)
        term_4 = head_list.tau * (head_list_query.tau - ((1 - head_list_query.tau) / (head_list_query.kappa_q - 1)))
        self.probability = (term_1 - term_2 - term_3) / term_4

    def calculate_variance_relative_to(self, other_query_url_mapping, query_str='*', url_str='*', r_c_q_u=0.0, head_list=None):
        other_query = other_query_url_mapping[query_str]
        head_list_query = head_list[query_str]
        # from Figure 5, line 17
        # broken down into separate steps to help clarity
        term_1 = r_c_q_u * (1.0 - r_c_q_u) / (other_query_url_mapping.number_of_query_url_pairs - 1.0)
        term_2a = 2.0 * other_query_url_mapping.number_of_query_url_pairs / (other_query_url_mapping.number_of_query_url_pairs - 1.0)
        # note t1 / t2 / t3 here instead of the equivalent t1 / (t2 * t3)
        term_2b = (1.0 - head_list.tau) / (head_list.kappa - 1.0) / head_list_query.kappa_q
        term_2c = (head_list.tau - head_list.tau * head_list_query.tau) / (head_list_query.kappa_q - 1.0)
        term_2d = r_c_q_u * (head_list.kappa - 2.0 + head_list.tau) / (head_list.kappa * head_list.tau - 1.0)
        term_2 = term_2a * (term_2b - term_2c) * term_2d
        # note t1 / t2 / t3 here instead of the equivalent t1 / (t2 * t3)
        term_3a = (1.0 - head_list.tau) / (head_list.kappa - 1.0) / head_list_query.kappa_q
        term_3b = pow((head_list.tau - head_list.tau * head_list_query.tau) / (head_list_query.kappa_q - 1.0), 2)
        term_3 = (term_3a - term_3b) * other_query.variance
        term_4 = 1.0 / pow(head_list.tau, 2) / pow(head_list_query.tau - ((1.0 - head_list_query.tau)/(head_list_query.kappa_q - 1.0)), 2)
        self.variance = (term_1 + term_2 + term_3) * term_4


# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value

class ClientQuery(Query):
    def __init__(self, config):
        super(ClientQuery, self).__init__(config)
        self.probability = 0.0  # TODO
        self.variance = 0.0  # TODO

    def calculate_probabilities_relative_to(self, other_query_url_mapping, query_str, head_list=None):
        # from Figure 5, line 11
        fraction_of_this_query_in_other_mapping = (
            other_query_url_mapping[query_str].number_of_urls / other_query_url_mapping.number_of_query_url_pairs
        )
        ratio = (1.0 - head_list.tau) / (head_list.kappa - 1.0)
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
            (other_query_url_mapping.number_of_query_url_pairs - 1)
        )

        # from Figure 5, line 14
        for url_str in head_list[query_str]:
            other_url = other_query_url_mapping[query_str][url_str]
            # Figure 5, line 15
            r_c_q_u = other_url.number_of_urls / other_query_url_mapping.number_of_query_url_pairs  # TODO: rename
            # Figure 5, line 16 implemented in the
            self[query_str][url_str].calculate_probability_relative_to(
                other_query_url_mapping,
                query_str=query_str,
                url_str=url_str,
                r_c_q_u=r_c_q_u,
                head_list=None
            )
            self[query_str][url_str].calculate_variance_relative_to(
                other_query_url_mapping,
                query_str=query_str,
                url_str=url_str,
                r_c_q_u=r_c_q_u,
                head_list=None
            )


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value

class ClientQueryCollection(QueryCollection):

    def calculate_probabilities(self, head_list):
        """This is from the Blender paper, Figure 4"""
        assert head_list.number_of_queries >= self.number_of_queries
        assert head_list.number_of_query_url_pairs >= self.number_of_query_url_pairs

        # we want the client probabilities calcualated relative to itself.
        self.calculate_probabilities_relative_to(self, head_list=head_list)

