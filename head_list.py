
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
    Query,
    QueryCollection
)


# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes

# none defined - this means that the classes from in_memory_structures are likely to be used

# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value

class HeadListQuery(Query):
    def __init__(self, config):
        super(HeadListQuery, self).__init__(config)
        self.tau = 0.0

    def calculate_tau(self):
        self.tau = (
            (exp(self.config.epsilon_prime_u) + (self.config.delta_prime_u / 2.0) * (self.count - 1.0))
            /
            (exp(self.config.epsilon_prime_u) + self.count - 1.0)
        )

    def subsume(self, query, url_str):
        # this method does not have to chain the subsume down the inheritance heirarchy nor the
        # containment heirarchy because the headlist only limits the count of a <q, u> pair to one
        # instance.
        url_stats = query[url_str]
        self.probability += url_stats.probability
        url_stats.probability = 0.0

    def calculate_probability_relative_to(self, other_query_url_mapping, query_str="*", b=0.0, head_list=None):
        for url in self.keys():
            self[url].calculate_probability_relative_to(
                other_query_url_mapping,
                query_str=query_str,
                url_str=url,
                b=self.config.b_t,
            )
            self.update_probability(self[url])
            # the original algorthim in Figure 4 calculated o_2 (sigma/variance) at this point.
            # However, in that algorithm most of those values will be thrown away without being used.
            # We'll delay calculating them until we know which records we're keeping.

    def print(self, indent):
        print('{}tau={}'.format(' ' * indent, self.tau))
        super(HeadListQuery, self).print(indent)


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value

class HeadList(QueryCollection):
    """This class add the Blender algorithmic parts to the highest level of Mapping of Mappings"""
    required_config = Namespace()
    required_config.add_option(
        "m",
        default=1000,
        doc="maximum size of the final headlist",
    )
    required_config.add_aggregation(
        "b_s",  # from Figure #3, line 6
        lambda config, local_config, arg: 2.0 * config.m_o / config.epsilon
    )
    required_config.add_aggregation(
        "tau",  # from Figure #3, line 7
        lambda config, local_config, arg: (
            (2.0 * config.m_o / config.epsilon)
            *
            (ln(exp(config.epsilon/2.0) + config.m_o - 1.0) - ln(config.delta))
        )
    )
    required_config.add_aggregation(
        "b_t",  # from Figure #4, line 9 - notice same definition as "b_s"
        lambda config, local_config, arg: 2.0 * config.m_o / config.epsilon
    )

    def __init__(self, config):
        super(HeadList, self).__init__(config)
        # ultimately, this collection will have to be truncated to a smaller size where retained members
        # will be those with the highest value of some statistic. Rather than sort at the end, this keeps
        # an index based on the statistic.
        self.probability_sorted_index = SortedDictOfLists()
        self.tau = 0.0

    def create_headlist(self, optin_database_s):
        """this is the implementation of the Figure 3 CreateHeadList from the Blender paper"""
        # Figure 3, line 6-7 were moved to configuration of this object
        # from Figure 3, CreateHeadList, line 7
        assert self.config.tau >= 1.0
        for query_str, url_str in optin_database_s.iter_records():
            y = laplace(self.config.b_s)  # TODO: understand and select correct parameter
            if optin_database_s[query_str][url_str].count + y > self.config.tau:
                self.add((query_str, url_str))
        print('adding <*, *> in create_headlist')
        self.add(('*', '*'))
        #self['*'].touch('*')  # add <*, *> with a count of 0

    def calculate_probabilities_relative_to(self, other_query_url_mapping):
        """This is from the Blender paper, Figure 4"""
        # Figure 4: lines 10 - 12
        for query_str in self.keys():
            self[query_str].calculate_probability_relative_to(
                other_query_url_mapping,
                query_str=query_str,
                b=self.config.b_t,
            )
            if query_str != '*':
                # we don't need to index the <*, *> case
                self.probability_sorted_index[self[query_str].probability].append(query_str)

    def subsume_entries_beyond_max_size(self):
        """This is part of the algorithm from the Blender paper, Figure 4"""
        # Figure 4: line 14
        to_be_deleted_list = []
        if '*' not in self:
            print('adding <*, *> in subsume_entries_beyond_max_size')
            self.add(('*', '*'))
        for i, (probability, query_str) in enumerate(self.probability_sorted_index.iter_records()):
            print("{} head_list.count {} {}".format(i, self.count, query_str))
            if i >= self.config.m:
                the_query = self[query_str]
                for url_str in the_query.keys():
                    print('subsuming <{}, {}>'.format(query_str, url_str))
                    print('before <*, *> count {}'.format(self['*']['*'].count))
                    print('before * count {}'.format(self['*'].count))
                    self.probability_sorted_index[the_query.probability].remove(query_str)
                    self['*'].subsume(the_query, url_str)
                    self.probability_sorted_index[the_query.probability].append(query_str)
                    print('after <*, *> count {}'.format(self['*']['*'].count))
                    print('after * count {}'.format(self['*'].count))
                    # we need to remove the <q, u> pair but cannot do so while the collection is
                    # in iteration.  We keep a list of <q, u> pairs to remove and delete them after
                    # iteration is complete
                    to_be_deleted_list.append((query_str, url_str))
        for query_str, url_str in to_be_deleted_list:
            del self[query_str][url_str]
            if not len(self[query_str]):
                del self[query_str]

    def calculate_variance_relative_to(self, other_query_url_mapping):
        """This is part of the algorithm from the Blender paper, Figure 4"""
        # Figure 4: line 15 & 13
        b_t = 2.0 * self.config.m_o / self.config.epsilon
        for query_str, url_str in self.iter_records():
            self[query_str][url_str].calculate_variance_relative_to(
                other_query_url_mapping,
                query_str=query_str,
                url_str=url_str,
                b_t=b_t
            )

    def calculate_tau(self):
        """from Figure 6 LocalAlg, lines 4-6"""
        self.tau = (
            (exp(self.config.epsilon_prime_q) + (self.config.delta_prime_q / 2.0) * (self.count - 1))
            /
            (exp(self.config.epsilon_prime_q) + self.count - 1)
        )
        for query_str in self.keys():
            self[query_str].calculate_tau()

    def print(self, indent=0):
        print('{}config.tau={}'.format(' ' * indent, self.config.tau))
        print('{}tau={}'.format(' ' * indent, self.tau))
        super(HeadList, self).print(indent)

    def export_for_client_distribution(self):
        # this ought to produce a json file without the probabilites and variance data
        for query_str in self.keys():
            pass

    def __getstate__(self, key_list=None):
        # for use by jsonpickle
        if key_list is None:
            key_list = list()
        key_list.append('probability_sorted_index')
        return super(HeadList, self).__getstate__(key_list)

