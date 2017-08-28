from collections import (
    defaultdict,
    MutableMapping
)

from functools import partial

from configman import (
    configuration,
    Namespace,
    RequiredConfig,
    class_converter,
)


class URLStatsCounter(RequiredConfig):
    def __init__(self, config, count=0):
        self.config = config
        self.count = count

    def increment_count(self, amount=1):
        self.count += amount

    def subsume(self, other_URLStatsCounter):
        self.count += other_URLStatsCounter.count


class URLStatsCounterWithProbability(URLStatsCounter):
    def __init__(self, config):
        super(URLStatsCounterWithProbability, self).__init__(config)
        self.p = 0;
        self.o = 0;

    def subsume(self, other_URLStatsCounter):
        super(URLStatsCounterWithProbability, self).subsume(other_URLStatsCounter)
        self.p += other_URLStatsCounter.p
        #self.o =  # TODO: what here?


class URLStatusMappingClass(MutableMapping, RequiredConfig):
    """A mapping of URLs to URL stats classes"""
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

    def touch(self, url):
        """add a url without incrementing the count - this is used to add the star url *"""
        self.urls[url]

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


class QueryURLMappingClass(MutableMapping, RequiredConfig):
    """a mapping of queries to URL mappings"""
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

    def add(self, q_u_tuple):
        self.queries_and_urls[q_u_tuple[0]].add(q_u_tuple[1])

    def subsume_those_not_present(self, other_query_url_mapping):
        to_be_deleted_list = []
        for q, u in self.items():
            if (q, u) not in other_query_url_mapping:
                self['*']['*'].subsume(self[q][u])
                to_be_deleted_list.append((q, u))
        for q, u in to_be_deleted_list:
            del self[q][u]
            del self[q]


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

    def iter_records(self):
        for a_query, url_mapping in self.items:
            for a_url in url_mapping.keys:
                yield a_query, a_url

    # domain actions
    def add_url_star_to_all_entries(self):
        for a_url_collecton in self.values():
            a_url_collecton.touch('*')



required_config = Namespace()
required_config.add_option(
    name="headlist_base",
    default=QueryURLMappingClass,
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as the base class for HeadList"
)
required_config.add_option(
    "epsilon",
    default=4.0,
    doc="epsilon",
)
required_config.add_option(
    "delta",
    default=0.000001,
    doc="delta",
)
required_config.add_option(
    "m_o",
    default=10,
    doc="maximum number of records per opt-in user",
)

from math import (
    log as ln,
    exp
)
from numpy.random import (
    laplace
)


def createHeadList(config, optin_database):
    class HeadList(config.headlist_base):
        def __init__(self, config, optin_database):
            super(config.headlist_base, self).__init__(config)
            self.optin_database = optin_database
            self.epsilon = config.epsilon
            self.delta = config.delta
            self.m_o = config.m_o

            b_s = 2 * self.m_o / self.epsilon
            # from Figure 3, CreateHeadList, line 7
            sigma = b_s * (ln(exp(self.epsilon/2) + self.m_o - 1) - ln(self.delta))
            assert sigma >= 1
            for query, url in optin_database:
                y = laplace(b_s)  # TODO: understand and select correct parameter
                if optin_database[query][url].count > sigma:
                    self.add((query, url))
            self.add(('*', '*'))

    return HeadList(config, optin_database)
