from numpy.random import (
    random,
    laplace,
    choice,
)

from in_memory_structures import (
    URLCounter,
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
            # there is confusing on the significance of a database structure has only unqiue <q, u> pairs
            # or duplicates.  Some code clearly allows duplicates.  the definiton of |D| is for unique or
            # with duplicates?
            a_query = choice(head_list.keys())

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

