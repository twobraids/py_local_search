from blender.in_memory_structures import (
    URLStats,
    Query,
    QueryCollection
)
from blender.sorted_dict_of_lists import (
    SortedDictOfLists
)


# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes
class FinalURLStats(URLStats):
    def __init__(self, config, count=0):
        super(FinalURLStats, self).__init__(config, count)

    def calculate_probability_relative_to(self, other_query_url_mapping, query_str='*', url_str='*', head_list=None):
        client_query = other_query_url_mapping[query_str]
        client_url = client_query[url_str]
        head_list_query = head_list[query_str]
        head_list_url = head_list_query[url_str]
        # from Figure 7, line 3
        self.omega = client_url.variance / (head_list_url.variance + client_url.variance)
        self.probability = self.omega * head_list_url.probability + (1 - self.omega) * client_url.probability


# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value
class FinalQuery(Query):
    def __init__(self, config):
        super(FinalQuery, self).__init__(config)
        self.probability_sorted_index = SortedDictOfLists()

    def calculate_probability_relative_to(self, client_probabilities, optin_probabilities, query_str):
        for url_str in optin_probabilities[query_str].keys():
            a_url = self[url_str]
            a_url.calculate_probability_relative_to(client_probabilities, query_str, url_str, optin_probabilities)
            self.probability_sorted_index[a_url.probability].append(url_str)

    def iter_in_order(self):
        for a_probability, a_url_str in self.probability_sorted_index.iter_records():
            yield a_url_str


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value
class FinalQueryCollection(QueryCollection):

    def calculate_probability_relative_to(self, client_probabilities, optin_probabilities):
        for query_str in optin_probabilities.keys():
            a_query = self[query_str]
            a_query.calculate_probability_relative_to(client_probabilities, optin_probabilities, query_str)

    def iter_records(self):
        for query_str in self.keys():
            a_query = self[query_str]
            for a_url_str in a_query.iter_in_order():
                yield query_str, a_url_str

    def write(self, filename):
        with open(filename, encoding='utf-8', mode="w") as f:
            for query, url in self.iter_records():
                probability = self[query][url].probability
                if url == '*' and probability == 0:
                    continue
                f.write('{} {} {}\n'.format(query, url, probability))
