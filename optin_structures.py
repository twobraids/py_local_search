from collections import (
    defaultdict,
    MutableMapping
)
from sorted_dict_of_lists import (
    SortedDictOfLists
)

from functools import partial

from math import (
    log as ln,
    exp
)
from numpy.random import (
    laplace
)

from configman import (
    configuration,
    Namespace,
    RequiredConfig,
    class_converter,
)

# The Blender algorithm represents its major data structures with nested mappings of mappings
# even though they're referred to as vectors or tables.  In the original C# code, these were
# implemented as basic Dictionaries mapping strings to strings or strings to scalars.
# Operations on these data structures are not attached to the data structures as instance
# methods, but as external functions.

# In this implementation, I've taken a more traditional object oriented approach in defining
# classes to represent the different levels the mappings.  Rather than using separate
# functions for operations,  I've used instance methods to associate function to data.
# I believe this gives a more flexible design where implementation details are tied more
# tightly to the actual implementation.  This leads to being able to create alternative
# implementations that facilitate scaling.  This design allows the data to be re-implemented
# in, for example, a relational database.

class URLStatsCounter(RequiredConfig):
    """Lowest level of the nested mappings. This is the data associated with a URL.
    This data structure will likely be modified to include page title and excerpt
    at sometime in the future.
    """
    def __init__(self, config, count=0):
        self.config = config  # constants and configuration
        self.count = count  # number of repeats of this URL
        self.rho = 0  # the computed probability of this URL
        self.sigma = 0  # the variance of this URL

    def increment_count(self, amount=1):
        self.count += amount

    def subsume(self, other_URLStatsCounter):
        self.count += other_URLStatsCounter.count
        self.rho += other_URLStatsCounter.rho
        # self.sigma   # take no action, will be calculated else where

    def calculate_probability_relative_to(self, b, query, url, other_query_url_mapping):
        y = laplace(b)  # TODO: understand and select correct parameter
        self.rho = (
            (other_query_url_mapping[query][url].count * y) / other_query_url_mapping.count
        )

    def calculate_variance_relative_to(self, b_t, query, url, other_query_url_mapping):
        self.sigma = (
            (self.rho * (1 - self.rho)) / (other_query_url_mapping.count - 1)
            +
            (2.0 * b_t * b_t) / (other_query_url_mapping.count * (other_query_url_mapping.count - 1))
        )


class URLStatusMappingClass(MutableMapping, RequiredConfig):
    """A mapping of URLs to URL stats classes.  The keys are URLs as strings and the values
    are instances of the class representing the URL data and stats.
    """
    required_config = Namespace()
    required_config.add_option(
        name="url_stats_class",
        default="working_structures.URLStats",
        from_string_converter=class_converter,
        doc="dependency injection of a class to represent statistics for URLs"
    )

    def __init__(self, config):
        self.config = config
        self.urls = defaultdict(partial(self.config.url_stats_class, self.config))
        self.probability = 0

    def touch(self, url):
        """add a url without incrementing the count - this is used to add the star url *"""
        self.urls[url]

    def subsume(self, url, url_stats):
        self[url].subsume(url_stats)
        self.probability += url_stats.rho

    def update_probability(self, url_stats):
        self.probability += url_stats.rho

    def add(self, url):
        self.urls[url].increment_count()

    def __getitem__(self, query):
        return self.urls[query]

    def __setitem__(self, url, item):
        self.urls[url] = item

    def __delitem__(self, url):
        del self.urls[url]

    def __iter__(self):
        for key in self.urls:
            yield key

    def __len__(self):
        return len(self.urls)

    def __contains__(self, key):
        return key in self.urls


class QueryURLMappingClass(MutableMapping, RequiredConfig):
    """This is the top of the mappings of mappings. The keys are queries and the values are
    instances of a mapping of URLs to URL statistics"""
    required_config = Namespace()
    required_config.add_option(
        name="url_mapping_class",
        default="URLStatusMappingClass",
        from_string_converter=class_converter,
        doc="dependency injection of a class to represent a mapping of URLs to URL stats objects"
    )
    def __init__(self, config):
        self.config = config
        # use dependency injection to create a dictionary keyed by query to values specified
        # represented by a URL class.  The 'defaultdict' constructor needs to have reference to
        # to a function to create instances of the value class of the dictionary.  Using 'partial'
        # allows the instantiated URL class to use dependency injection too, by passing the
        # the configuration in during instantiation
        self.queries_and_urls = defaultdict(partial(self.config.url_mapping_class, self.config))
        self.count = 0

    def add(self, q_u_tuple):
        """add a new <q, u> tuple to this collecton"""
        self.queries_and_urls[q_u_tuple[0]].add(q_u_tuple[1])
        self.count += 1

    def subsume_those_not_present_in(self, other_query_url_mapping):
        """take all <q, u> records in this collection that are not in the other_query_url_mapping and
        merge their statistics into ths collection's <*, *> entry"""
        to_be_deleted_list = []
        if '*' not in self.queries_and_urls:
            self['*'].touch('*')
        for query, url in self.iter_records():
            if query == '*':
                continue
            if query not in other_query_url_mapping or url not in other_query_url_mapping[query]:
                self['*']['*'].subsume(self[query][url])
                # we need to remove the <q, u> pair but cannot do so while the collection is
                # in iteration.  We keep a list of <q, u> pairs to remove and delete them after
                # iteration is complete
                to_be_deleted_list.append((query, url))
        for query, url in to_be_deleted_list:
            del self[query][url]
            if not len(self[query]):
                del self[query]

    def iter_records(self):
        """an alternative iterator that returns unique <q, u> pairs"""
        for a_query, url_mapping in self.items():
            for a_url in url_mapping.keys():
                yield a_query, a_url


    # this class implements the MuteableMapping Abstract Base Class.  These are the implementation of
    # the required methods for that ABC.
    def __getitem__(self, query):
        return self.queries_and_urls[query]

    def __setitem__(self, query, url):
        self.queries_and_urls[query] = url

    def __delitem__(self, query):
        del self.queries_and_urls[query]

    def __iter__(self):
        for key in self.queries_and_urls:
            yield key

    def __len__(self):
        return len(self.queries_and_urls)

    def __contains__(self, key):
        return key in self.queries_and_urls


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
                # the original algorthim in Figure 4 calculated o_2 (sigma) at this point.  However,
                # in that algorithm most of those values will be thrown away without being used.
                # We'll delay calculating them until we know which records we're keeping.
            if query != '*':
                # we don't need to index the <*, *> case
                self.probability_sorted_index[self[query].probability].append(query)

    def subsume_entries_beyond_max_size(self):
        """This is part of the algorithm from the Blender paper, Figure 4"""
        # Figure 4: line 14
        to_be_deleted_list = []
        if '*' not in self:
            self['*'].touch('*')
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
