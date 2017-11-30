from blender.in_memory_structures import (
    URLStats,
    QueryCollection
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
        try:
            self.omega = client_url.variance / (head_list_url.variance + client_url.variance)
        except ZeroDivisionError:  # TODO: eliminate
            print('<{}, {}>'.format(query_str, url_str))
            print("Divide by zero: head_list_url.variance:{}  client_url.variance:{}".format(head_list_url.variance, client_url.variance))
            exit(-1)
        self.probability = self.omega * head_list_url.probability + (1 - self.omega) * client_url.probability


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

class FinalQueryCollection(QueryCollection):

    def write(self, filename):
        with open(filename, encoding='utf-8', mode="w") as f:
            for query, url in self.iter_records():
                probability = self[query][url].probability
                if probability != 0:
                    f.write('{} {} {}\n'.format(query, url, probability))
