
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

from collections import (
    defaultdict,
    MutableMapping
)
from functools import partial
from configman import (
    Namespace,
    RequiredConfig,
    class_converter,
)

from numpy.random import (
    laplace
)

import json


class JsonPickleBase(object):
    # for use by jsonpickle
    def __getstate__(self, key_list=None):
        if key_list is None:
            key_list = list()
        key_list.append('config')
        state = self.__dict__.copy()
        for key in key_list:
            try:
                del state[key]
            except KeyError:
                pass
        return state


# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes
class URLStats(JsonPickleBase):
    """Lowest level of the nested mappings. This is the data associated with a URL.
    This data structure will likely be modified to include page title and excerpt
    at sometime in the future.
    """
    def __init__(self, config, count=0):
        self.config = config  # constants and configuration
        self.number_of_repetitions = count  # number of repeats of this URL
        self.probability = 0.0  # the computed probability of this URL
        self.variance = 0.0  # the variance of this URL

    def increment_count(self, amount=1):
        self.number_of_repetitions += amount

    def subsume(self, other_URLStats):
        self.number_of_repetitions += other_URLStats.number_of_repetitions
        self.probability += other_URLStats.probability
        other_URLStats.number_of_repetitions = 0
        other_URLStats.probability = 0.0

    def print(self, indent=0):
        print('{}count={}'.format(' ' * indent, self.number_of_repetitions))
        print("{}prob={}".format(' ' * indent, self.probability))
        print("{}vari={}".format(' ' * indent, self.variance))

    def calculate_probability_relative_to(self, other_query_url_mapping, query_str="*", url_str="*", b=0.0, head_list=None):
        y = laplace(b)  # TODO: understand and select correct parameter
        self.probability = (
            (other_query_url_mapping[query_str][url_str].number_of_repetitions + y) / other_query_url_mapping.number_of_query_url_pairs
        )

    def calculate_variance_relative_to(self, other_query_url_mapping, query_str='*', url_str='*', b_t=0.0):
        self.variance = (
            (self.probability * (1.0 - self.probability)) / (other_query_url_mapping.number_of_query_url_pairs - 1.0)
            +
            (2.0 * b_t * b_t) / (other_query_url_mapping.number_of_query_url_pairs * (other_query_url_mapping.number_of_query_url_pairs - 1.0))
        )


# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value

class Query(MutableMapping, JsonPickleBase, RequiredConfig):
    """A mapping of URLs to URL stats classes.  The keys are URLs as strings and the values
    are instances of the class representing the URL data and stats.
    """
    required_config = Namespace()
    required_config.add_option(
        name="url_stats_class",
        default="blender.in_memory_structures.URLStats",
        from_string_converter=class_converter,
        doc="dependency injection of a class to represent statistics for URLs"
    )

    def __init__(self, config):
        self.config = config
        self.urls = defaultdict(partial(self.config.url_stats_class, self.config))
        self.number_of_urls = 0
        self.probability = 0
        self.variance = 0

    def touch(self, url):
        """add a url without incrementing the count - this is used to add the star url *"""
        self.urls[url]

    def subsume(self, query, url_str):
        url_stats = query[url_str]
        self.number_of_urls += url_stats.number_of_repetitions
        self.probability += url_stats.probability
        #self.variance
        query.number_of_urls -= url_stats.number_of_repetitions
        query.probability -= url_stats.probability
        self['*'].subsume(url_stats)

    def update_probability(self, url_stats):
        # used by HeadList object
        self.probability += url_stats.probability

    def add(self, url):
        self.urls[url].increment_count()
        self.number_of_urls += 1

    def print(self, indent):
        print('{}count={}'.format(' ' * indent, self.number_of_urls))
        print('{}prob={}'.format(' ' * indent, self.probability))
        print('{}vari={}'.format(' ' * indent, self.variance))
        for url in self:
            print('{}{}'.format(' ' * indent, url))
            self[url].print(indent + 4)

    def __getitem__(self, query_str):
        return self.urls[query_str]

    def __setitem__(self, url, item):
        try:
            self.number_of_urls -= self.urls[url].number_of_repetitions
        except KeyError:
            pass
        self.urls[url] = item
        self.number_of_urls += item.number_of_repetitions

    def __delitem__(self, url):
        del self.urls[url]

    def __iter__(self):
        for key in self.urls:
            yield key

    def __len__(self):
        return len(self.urls)

    def __contains__(self, key):
        return key in self.urls


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value

class QueryCollection(MutableMapping, JsonPickleBase, RequiredConfig):
    """This is the top of the mappings of mappings. The keys are queries and the values are
    instances of a mapping of URLs to URL statistics"""
    required_config = Namespace()
    required_config.add_option(
        name="query_class",
        default="blender.in_memory_structures.Query",
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
        self.queries = defaultdict(partial(self.config.query_class, self.config))
        self.number_of_query_url_pairs = 0

    def append_star_values(self):
        # from 1-3 of EstimateClientProbabilities Figure 5.
        for query_str in self.queries:
            self[query_str].touch('*')

    def add(self, q_u_tuple):
        """add a new <q, u> tuple to this collecton"""
        q, u = q_u_tuple
        self.queries[q].add(u)
        self.number_of_query_url_pairs += 1

    def subsume_those_not_present_in(self, other_query_collection):
        """take all <q, u> records in this collection that are not in the other_query_url_mapping and
        merge their statistics into this collection's <*, *> entry"""
        to_be_deleted_list = []
        if '*' not in self.queries:
            self['*'].touch('*')
        for query_str, url_str in self.iter_records():
            if query_str == '*':
                continue
            if query_str not in other_query_collection or url_str not in other_query_collection[query_str]:
                self['*'].subsume(self[query_str], url_str)
                # we need to remove the <q, u> pair but cannot do so while the collection is
                # in iteration.  We keep a list of <q, u> pairs to remove and delete them after
                # iteration is complete
                to_be_deleted_list.append((query_str, url_str))
        for query_str, url_str in to_be_deleted_list:
            del self[query_str][url_str]
            if not len(self[query_str]):
                del self[query_str]

    def iter_records(self):
        """an alternative iterator that returns unique <q, u> pairs"""
        for a_query, url_mapping in self.items():
            for a_url in url_mapping.keys():
                yield a_query, a_url

    def load(self, file_name):
        with open(file_name, encoding='utf-8') as optin_data_source:
            for record_str in optin_data_source:
                record = json.loads(record_str)
                self.add(record)

    def print(self, indent=0):
        print('{}count={}'.format(' ' * indent, self.number_of_query_url_pairs))
        for query_str in self:
            print('{}{}'.format(' ' * indent, query_str))
            self[query_str].print(indent + 4)

    # this class implements the MuteableMapping Abstract Base Class.  These are the implementation of
    # the required methods for that ABC.
    def __getitem__(self, query_str):
        return self.queries[query_str]

    def __setitem__(self, query_str, url):
        self.queries[query_str] = url

    def __delitem__(self, query_str):
        del self.queries[query_str]

    def __iter__(self):
        for key in self.queries:
            yield key

    def __len__(self):
        return len(self.queries)

    def __contains__(self, key):
        return key in self.queries

