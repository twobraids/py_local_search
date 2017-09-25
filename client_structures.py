from numpy.random import (
    laplace
)

from in_memory_structures import (
    URLCounter,
)


class URLStatsForClient(URLCounter):
    def __init__(self, config, count=0):
        super(URLStatsForClient, self).__init__(config, count)
        self.probability = 0  # the computed probability of this URL
        self.variance = 0  # the variance of this URL

    #def subsume(self, other_URLStatsCounter):
        #super(URLStatsForOptin, self).subsume(other_URLStatsCounter)
        #self.probability += other_URLStatsCounter.probability
        ## self.sigma   # take no action, will be calculated else where

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

