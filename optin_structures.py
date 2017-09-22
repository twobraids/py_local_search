from blender.sorted_dict_of_lists import (
    SortedDictOfLists
)

from math import (
    log as ln,
    exp
)
from numpy.random import (
    laplace
)

from configman import (
    Namespace
)

from blender.in_memory_structures import (
    URLCounter,
    QueryURLMappingClass
)


class URLStatsForOptin(URLCounter):
    def __init__(self, config, count=0):
        super(URLStatsForOptin, self).__init__(config, count)
        self.probability = 0  # the computed probability of this URL
        self.variance = 0  # the variance of this URL

    def subsume(self, other_URLStatsCounter):
        super(URLStatsForOptin, self).subsume(other_URLStatsCounter)
        self.probability += other_URLStatsCounter.probability
        # self.sigma   # take no action, will be calculated else where

    def calculate_probability_relative_to(self, b, query, url, other_query_url_mapping):
        y = laplace(b)  # TODO: understand and select correct parameter
        self.probability = (
            (other_query_url_mapping[query][url].count * y) / other_query_url_mapping.count
        )

    def calculate_variance_relative_to(self, b_t, query, url, other_query_url_mapping):
        self.variance = (
            (self.probability * (1 - self.probability)) / (other_query_url_mapping.count - 1)
            +
            (2.0 * b_t * b_t) / (other_query_url_mapping.count * (other_query_url_mapping.count - 1))
        )


class HeadList(QueryURLMappingClass):
    """This class add the Blender algorithmic parts to the highest level of Mapping of Mappings"""
    required_config = Namespace()
    required_config.add_option(
        "m",
        default=1000,
        doc="maximum size of the final headlist",
    )

    def __init__(self, config):
        super(HeadList, self).__init__(config)
        # ultimately, this collection will have to be truncated to a smaller size where retained members
        # will be those with the highest value of some statistic. Rather than sort at the end, this keeps
        # an index based on the statistic.
        self.probability_sorted_index = SortedDictOfLists()

    def create_headlist(self, optin_database_s):
        """this is the implementation of the Figure 3 CreateHeadList from the Blender paper"""
        b_s = 2.0 * self.config.m_o / self.config.epsilon
        # from Figure 3, CreateHeadList, line 7
        tau = b_s * (ln(exp(self.config.epsilon/2.0) + self.config.m_o - 1.0) - ln(self.config.delta))
        assert tau >= 1
        for query, url in optin_database_s.iter_records():
            y = laplace(b_s)  # TODO: understand and select correct parameter
            if optin_database_s[query][url].count + y > tau:
                self.add((query, url))
        self['*'].touch('*') # add <*, *> with a count of 0

    def calculate_probabilities_relative_to(self, other_query_url_mapping):
        """This is from the Blender paper, Figure 4"""
        # Figure 4: lines 9 - 12
        b_t = 2.0 * self.config.m_o / self.config.epsilon
        for query in self.keys():
            for url in self[query].keys():
                self[query][url].calculate_probability_relative_to(b_t, query, url, other_query_url_mapping)
                self[query].update_probability(self[query][url])
                # the original algorthim in Figure 4 calculated o_2 (sigma/variance) at this point.
                # However, in that algorithm most of those values will be thrown away without being used.
                # We'll delay calculating them until we know which records we're keeping.
            if query != '*':
                # we don't need to index the <*, *> case
                self.probability_sorted_index[self[query].probability].append(query)

    def subsume_entries_beyond_max_size(self):
        """This is part of the algorithm from the Blender paper, Figure 4"""
        # Figure 4: line 14
        to_be_deleted_list = []
        if '*' not in self:
            self['*'].touch('*')  # create the entry with a count of zero
        for i, (probability, query) in enumerate(self.probability_sorted_index.iter_records()):
            if i >= self.config.m:
                for url in self[query].keys():
                    self['*'].subsume('*', self[query][url])
                    # we need to remove the <q, u> pair but cannot do so while the collection is
                    # in iteration.  We keep a list of <q, u> pairs to remove and delete them after
                    # iteration is complete
                    to_be_deleted_list.append((query, url))
        for query, url in to_be_deleted_list:
            del self[query][url]
            if not len(self[query]):
                del self[query]

    def calculate_variance_relative_to(self, other_query_url_mapping):
        """This is part of the algorithm from the Blender paper, Figure 4"""
        # Figure 4: line 15 & 13
        b_t = 2.0 * self.config.m_o / self.config.epsilon
        for query, url in self.iter_records():
            self[query][url].calculate_variance_relative_to(b_t, query, url, other_query_url_mapping)

    def export_for_client_distribution(self):
        # this ought to produce a json file without the probabilites and variance data
        for query in self.keys():
            pass

    def save(self):
        # the ought to create a json file with the probabilities and varance data
        pass

    def load(self):
        # populate a HeadList from a json fil
        pass





