from blender.in_memory_structures import (
    URLStatsWithProbability
)


# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes
class URLStatsForClient(URLStatsWithProbability):
    def __init__(self, config, count=0):
        super(URLStatsForClient, self).__init__(config, count)
        self.probability = 0.0  # the computed probability of this URL
        self.variance = 0.0  # the variance of this URL

    def calculate_probability_relative_to(self, other_query_url_mapping, query='*', url='*', head_list=None):
        client_query = other_query_url_mapping[query]
        client_url = client_query[url]
        head_list_query = head_list[query]
        head_list_url = head_list_query[url]
        # from Figure 7, line 3
        self.omega = client_url.variance / (head_list_url.variance + client_url.variance)
        self.probability = self.omega * head_list.probability + (1 - self.omega) * client_url.probability


# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value
