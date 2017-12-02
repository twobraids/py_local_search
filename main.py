#!/usr/bin/env python3

from configman import (
    configuration,
    command_line,
    ConfigFileFutureProxy as configuration_file,
    environment,
    Namespace,
    class_converter,
)

# define the constants used for the Blender algorithm as well as the classes for dependency injection

required_config = Namespace()

required_config.add_option(
    "epsilon",
    default=4.0,  # set from text, p11, 1st paragraph
    doc="epsilon",
)
required_config.add_option(
    "delta",
    default=0.000001,  # from text, p11, 1st paragraph
    doc="delta",
)
required_config.add_option(
    "m_o",
    default=1.0,
    doc="maximum number of records per opt-in user",
)

required_config.add_option(
    "m_c",
    default=1.0,
    doc="maximum number of records per client user",
)

required_config.add_option(
    "f_c",
    default=0.85,
    doc="the fraction of the privacy budget to allocate "
        "to reporting queries",
)

required_config.add_option(
    "optin_database_s_filename",
    default='optin_s.data.json',
    doc="the pathname of the optin_database_s formated as [query, url] pairs"
)

required_config.add_option(
    "optin_database_t_filename",
    default='optin_t.data.json',
    doc="the pathname of the optin_database_t json formated as [query, url] pairs"
)

required_config.add_option(
    "client_database_filename",
    default='client.data.json',
    doc="the pathname of the client_database json formated as [query, url] pairs"
)

required_config.add_option(
    "output_filename",
    default='out.data',
    doc="the pathname of the final probabilities output"
)


# the following are constants calculated in Figure 6 LocalAlg and then
# referenced in EstimateClientProbabilities Figure 5. While they are
# defined in functions, they really depend only on configuration and can
# therefore be calculated at program initialization time.
required_config.add_aggregation(
    "epsilon_prime",  # Figure 6 LocalAlg line 2
    lambda config, local_config, arg: config.epsilon / config.m_c
)
# because configman cannot guarantee the order of initialization of these
# aggregations, they cannot depend on each other.  That's why each has
# been rewritten from the original definitions in Figure 6 lines 2-3
required_config.add_aggregation(
    "epsilon_prime_q",  # Figure 6 LocalAlg line 3
    lambda config, local_config, arg: config.f_c * config.epsilon / config.m_c
)
required_config.add_aggregation(
    "epsilon_prime_u",  # Figure 6 LocalAlg line 3
    lambda config, local_config, arg: (config.epsilon / config.m_c) - (config.f_c * config.epsilon / config.m_c)
)

required_config.add_aggregation(
    "delta_prime",  # Figure 6 LocalAlg line 2
    lambda config, local_config, arg: config.delta / config.m_c
)
required_config.add_aggregation(
    "delta_prime_q",  # Figure 6 LocalAlg line 3
    lambda config, local_config, arg: config.f_c * config.delta / config.m_c
)
required_config.add_aggregation(
    "delta_prime_u",  # Figure 6 LocalAlg line 3
    lambda config, local_config, arg: (config.delta / config.m_c) - (config.f_c * config.delta / config.m_c)
)

# declare the types of the default data structures for use in dependency injection
required_config.namespace('optin_db')
required_config.optin_db.add_option(
    name="optin_db_class",
    default="blender.in_memory_structures.QueryCollection",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as non-headlist <q, u> databases"
)

required_config.namespace('head_list_db')
required_config.head_list_db.add_option(
    name="head_list_class",
    default="blender.head_list.HeadList",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as the HeadList"
)

required_config.namespace('client_db')
required_config.client_db.add_option(
    name="client_db_class",
    default="blender.in_memory_structures.QueryCollection",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as the Optin Database"
)

required_config.namespace('final_probabilities')
required_config.final_probabilities.add_option(
    name="final_probabilites_db_class",
    default="blender.head_list.HeadList",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve final probability vector"
)

# The Blender paper refers to several data structures as databases and vectors.
# However, digging deeper there is really only one data structure: a mapping of
# mappings to statistical data. The first mapping level uses queries as the key.
# Comments in this code will often refer to this level as "Top Level Structure"
# The second level of mapping uses urls for a key ("2nd Level Structure"). The
# lowest level values are just a tuple of stats ("3rd Level Structure").
#
# This implementation uses classes to represent each level of the mapping as well
# as the lowest level value.   The implementation classes vary based on the
# role that the data structure represents.
#
# For example, the "optin_db" is represented by using the Top Level Structure,
# "blender.optin_structures.QueryCollection", which is keyed by the query.
#
# optin_db['some query'] returns an instance of the 2nd level of the
# structure, an instance of "blender.in_memory_structures.Query".
# This is itself a mapping which is keyed by url.
#
# optin_db['some query']['some/url'] returns an instance of the 3rd level, a url
# stats object, "blender.in_memory_structures.URLStats".  This final
# lowest level object contains stats and methods for individual urls.
#
# this section consolidates the declaration of the mapping structures into
# one place.
#
# This structure will be given to the configuration system as the defaults for
# each use case.  The configuration system enables dependency injection.  Any
# of these values can be changed at program initialization time through command
# line options, environment variables or configuration file (in 'ini', 'conf' or
# 'json' form)

default_data_structures = {  # keyed by the use case
    "head_list_db": {
        # level 1
        "head_list_class": "blender.head_list.HeadList",
        # level 2
        "query_class": "blender.head_list.HeadListQuery",
        # level 3
        "url_stats_class": "blender.in_memory_structures.URLStats"
    },
    "optin_db": {
        # level 1
        "optin_db_class": "blender.in_memory_structures.QueryCollection",
        # level 2
        "query_class": "blender.in_memory_structures.Query",
        # level 3
        "url_stats_class": "blender.in_memory_structures.URLStats"
    },
    "client_db": {
        # level 1
        "client_db_class": "blender.client_structures.ClientQueryCollection",
        # level 2
        "query_class": "blender.client_structures.ClientQuery",
        # level 3
        "url_stats_class": "blender.client_structures.ClientURLStats"
    },
    "final_probabilities": {
        # level 1
        "final_probabilites_db_class": "blender.final_structures.FinalQueryCollection",
        # level 2
        "query_class": "blender.final_structures.FinalQuery",
        # level 3
        "url_stats_class": "blender.final_structures.FinalURLStats"
    },
}


# direct implementations of the Blender algorithms

# CreateHeadList from Figure 3
# The original name "CreateHeadList" is not very accurate as it
# only executes the first step in creation of the head_list
# that is distributed to the clients.  It is the method
# EstimateOptinProbabilities that actually creates the
# final version of the head_list.
def create_preliminary_headlist(config, optin_database_s):
    """
    Parameters:
        config -
        optin_database_s -
    """
    print('create_preliminary_headlist')
    preliminary_head_list = config.head_list_db.head_list_class(config.head_list_db)
    preliminary_head_list.create_headlist(optin_database_s)

    return preliminary_head_list


# EstimateOptinProbabilities from Figure 4
def estimate_optin_probabilities(preliminary_head_list, optin_database_t):
    """
    Parameters:
        preliminary_head_list -
        optin_database_t -
    """
    print('estimate_optin_probabilities')
    optin_database_t.subsume_those_not_present_in(preliminary_head_list)
    preliminary_head_list.calculate_probabilities_relative_to(optin_database_t)
    preliminary_head_list.subsume_entries_beyond_max_size()
    preliminary_head_list.calculate_variance_relative_to(optin_database_t)

    # this is from lines 1-3 of EstimateClientProbabilities Figure 5.
    # It has been moved out of that algorithm and placed here because
    # LocalAlg Figure 6 requires the star values be present when the client
    # is using the headlist.  If the action were left in EstimateClientProbabilities,
    # it would be too late.  The LocalAlg is executed in an asynchronous and
    # distributed manner after this method, estimate_optin_probabilities, but
    # before EstimateClientProbabilities.  Since this method prepares the head_list
    # for the client, it is best that the star values are added here.  The algorithm
    # calls for the <*, *> to be added, but in this implementation, that is
    # not needed as the previously executed routine subsume_entries_beyond_max_size
    # has already done this.
    preliminary_head_list.append_star_values()

    # this is from lines 4-6 of LocalAlg Figure 6.  The original Blender algorithms
    # call for each client to calculate kappa and tau for each query in the
    # headlist.  Further, the calculation is called for again in
    # EstimateClientProbablities Figure 5 line 8.  Since these are constant,
    # the calculation is moved here and the data stored with the rest of the
    # Headlist.
    preliminary_head_list.calculate_tau()

    # at this point the preliminary_head_list is the final headlist.  It includes
    # the vector of probabilities and variances along with the tau and kappa required
    # for further steps
    return preliminary_head_list


# EstimateClientProbabilities
def estimate_client_probabilities(config, head_list, client_database):
    """
    Parameters:
        head_list -
        client_database -
    """
    # lines 1-3 from Figure 5 have been executed at the end of the
    # function "estimate_optin_probabilities"

    # lines 4-7 from Figure 5 have been moved to the rountine that creates
    # the client database.  This allows the client database to be just passed in
    # as a parameter.

    # line 8 from Figure 5 defines a set of constants to be used through the body of the
    # function.  Because each of these constants is dependent solely on configuration
    # constants, their calculation was moved to the initialization of configuration
    # The constants can be accessed in configuration

    print('estimate_client_probabilities')

    client_database.calculate_probabilities(head_list)

    return client_database


# Blender merge
def blend_probabilities(config, optin_probabilities, client_probabilities):
    """
    Parameters:
        optin_probabilities -
        client_probabilities -
    """
    # the original code called for the optin_probabilities and the head_list as separate
    # entities.  They're much more easily stored in the same data structure to avoid a lot
    # duplicated keys and values.

    print('blend_probabilities')
    final_probabilities = config.final_probabilities.final_probabilites_db_class(
        config.final_probabilities
    )
    final_probabilities.calculate_probability_relative_to(client_probabilities, optin_probabilities)
    for query, url in optin_probabilities.iter_records():
        final_probabilities[query][url].calculate_probability_relative_to(
            client_probabilities,
            query_str=query,
            url_str=url,
            head_list=optin_probabilities,
        )

    return final_probabilities


if __name__ == "__main__":

    from functools import partial
    from collections import Mapping
    import json

    from configman.converters import (
        to_str
    )

    from blender.tests.client_support import local_alg

    def client_load_iter(file_name):
        with open(file_name, encoding='utf-8') as optin_data_source:
            for record_str in optin_data_source:
                record = json.loads(record_str)
                yield record

    def print_config(config, indent=0):
        keys = sorted(config.keys())
        namespaces = []
        for key in keys:
            if key.startswith('_') or key.startswith('admin') or key == 'help':
                continue
            value = config[key]
            if isinstance(value, Mapping):
                namespaces.append(key)
                continue
            print("{}{}: {}".format(' ' * indent, key, to_str(value)))
        for key in namespaces:
            value = config[key]
            print("{}{}:".format(' ' * indent, key))
            print_config(value, indent + 4)


    # this line handles getting configuration information from the command
    # line or any configuration files that might exist.

    # on the command line, typing --help will give an argparse-like listing
    # of all the configuration options defined with the recursive hierarchy
    # in the definition of "required_config"

    # The program can also write configuration files in various formats with
    # the command line argument --dump_config=file-name.type  where "type" is
    # "ini" for nested ini files, "conf" for flat key value pairs, "json"
    # for json compatible files, or "py" to write an initializing python module

    # Configuration files can be read by specifying "--conf=somefile.type"

    # Configuration can also be read from the working environment.  Since the
    # standard Linux commandline environment disallows "." in environment
    # variables, substitute the double underbar:
    #    export client_db.client_db_class=some.module.class  # fails
    #    export client_db__client_db_class=some.module.class  # works

    config = configuration(
        definition_source=required_config,
        values_source_list=[
            # create the overriding hierarchy for the sources of configuration.
            # each source will override values from sources higher in the list
            default_data_structures,
            environment,
            configuration_file,
            command_line,
        ]
    )
    print('config:')
    print_config(config, 4)
    print('---------------------')

    # create & read optin_database_s
    optin_database_s = config.optin_db.optin_db_class(
        config.optin_db
    )
    optin_database_s.load(config.optin_database_s_filename)

    print('optin_db_s:\n\tnumber_of_records:{}\n\tnumber_of_queries:{}'.format(optin_database_s.number_of_query_url_pairs, optin_database_s.number_of_queries))

    # create preliminary head list
    preliminary_head_list = create_preliminary_headlist(
        config,
        optin_database_s
    )
    print('preliminary_head_list:\n\tnumber_of_records:{}\n\tnumber_of_queries:{}'.format(preliminary_head_list.number_of_query_url_pairs, preliminary_head_list.number_of_queries))

    # create & read optin_database_t
    optin_database_t = config.optin_db.optin_db_class(
        config.optin_db
    )
    optin_database_t.load(config.optin_database_t_filename)
    print('optin_db_t:\n\tnumber_of_records:{}\n\tnumber_of_queries:{}'.format(optin_database_t.number_of_query_url_pairs, optin_database_t.number_of_queries))

    head_list_for_distribution = estimate_optin_probabilities(
        preliminary_head_list,
        optin_database_t
    )
    print('head_list_for_distribution:\n\tnumber_of_records:{}\n\tnumber_of_queries:{}'.format(head_list_for_distribution.number_of_query_url_pairs, head_list_for_distribution.number_of_queries))

    # create and load client database
    client_database = config.client_db.client_db_class(
        config.client_db
    )
    for record in local_alg(config, head_list_for_distribution, partial(client_load_iter, config.client_database_filename)):
        client_database.add(record)
    print('client_database:\n\tnumber_of_records:{}\n\tnumber_of_queries:{}'.format(client_database.number_of_query_url_pairs, client_database.number_of_queries))

    client_stats = estimate_client_probabilities(
        config,
        head_list_for_distribution,
        client_database
    )

    final_stats = blend_probabilities(
        config,
        head_list_for_distribution,
        client_stats
    )

    final_stats.write(config.output_filename)
