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

required_config.namespace('opt_in_db')
required_config.opt_in_db.add_option(
    name="optin_db_class",
    default="blender.in_memory_structures.QueryURLMappingClass",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as non-headlist <q, u> databases"
)

required_config.namespace('head_list_db')
required_config.head_list_db.add_option(
    name="headlist_class",
    default="blender.optin_structures.HeadList",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as the HeadList"
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

# the following are constants calculated in Figure 6 LocalAlg and then
# referenced in EstimateClientProbabilities Figure 5. While they are
# defined in functions, they really depend only on configuration and can
# therefore be calculated at program initialization time.

required_config.add_aggregation(
    "epsilon_prime",  # Figure 6 LocalAlg line 2
    lambda config: config.epsilon / config.m_c
)
required_config.add_aggregation(
    "epsilon_prime_q",  # Figure 6 LocalAlg line 3
    lambda config: config.f_c * config.epsilon / config.m_c
)
required_config.add_aggregation(
    "epsilon_prime_u",  # Figure 6 LocalAlg line 3
    lambda config: (config.epsilon / config.m_c) - (config.f_c * config.epsilon / config.m_c)
)

required_config.add_aggregation(
    "delta_prime",  # Figure 6 LocalAlg line 2
    lambda config: config.delta / config.m_c
)
required_config.add_aggregation(
    "delta_prime_q",  # Figure 6 LocalAlg line 3
    lambda config: config.f_c * config.delta / config.m_c
)
required_config.add_aggregation(
    "delta_prime_u",  # Figure 6 LocalAlg line 3
    lambda config: (config.delta / config.m_c) - (config.f_c * config.delta / config.m_c)
)


# setup default data structures
# Most of the major working data structures of this program are
# multilevel mappings where each level is represented by a different
# class.
# For example, the "optin_db" is represented by the
# "optin_structures.QueryURLMappingClass" which is keyed by the query.
# optin_db['some query'] returns an instance of the next level of the
# structure, an instance of "in_memory_structures.URLStatsMappingClass".
# This is itself a mapping which is keyed by url.
# optin_db['some query']['some/url'] returns an instance of a url
# stats object, "optin_structures.URLStatsForOptin".  This final
# lowest level object contains stats and methods for individual urls.
#
# There are several structures that follow this pattern, each selecting
# different implementation classes based on the role that the structure
# needs to play in the algorithm
#
# this section consolidates the declaration of the mapping structures into
# one place.

default_data_structures = {
    "head_list_db": {  # used for the preliminary_head_list & head_list
        "headlist_class": "blender.optin_structures.HeadList",
        "url_mapping_class": "blender.in_memory_structures.URLStatsMappingClass",
        "url_stats_class": "blender.optin_structures.URLStatsForOptin"
    },
    "optin_db": {  # used for the optin_database_s & optin_database_t
        "optin_db_class": "blender.optin_structures.QueryURLMappingClass",
        "url_mapping_class": "blender.in_memory_structures.URLStatsMappingClass",
        "url_stats_class": "blender.optin_structures.URLStatsForOptin"
    },
    "client_db": {
        "client_db_class": "blender.client_structures.ClientQueryURLMappingClass",
        "url_mapping_class": "blender.in_memory_structures.URLStatsMappingClass",
        "url_stats_class": "blender.client_structures.URLStatsForClient"
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
    preliminary_head_list = config.head_list_db.headlist_class(config.head_list_db)
    preliminary_head_list.create_headlist(optin_database_s)

    return preliminary_head_list


# EstimateOptinProbabilities from Figure 4
def estimate_optin_probabilities(preliminary_head_list, optin_database_t):
    """
    Parameters:
        preliminary_head_list -
        optin_database_t -
    """
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
    # for the client, it is best that the star values are added here.
    preliminary_head_list.append_star_values()

    return preliminary_head_list


# EstimateClientProbabilities
def estimate_client_probabilities(config, head_list, client_database):
    epsilon_prime = config.epsilon / config.m_c
    epsilon_prime_q = config.f_c * epsilon_prime
    epsilon_prime_u = config.epsilon - epsilon_prime_q

    delta_prime = config.delta / config.m_c
    delta_prime_q = config.f_c * delta_prime
    delta_prime_u = delta_prime - delta_prime_q


if __name__ == "__main__":
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
            # setup a structure of overriding hierarchy for the
            # sources of configuration information.
            # each source will override values from sources lower
            # in the list
            command_line,
            configuration_file,
            environment,
            default_data_structures
        ]
    )

    # create & read optin_database_s
    optin_database_s = config.opt_in_db.optin_db_class(
        config.opt_in_db
    )
    # optin_database_s.load("loadlocation_s")

    # create preliminary head list
    preliminary_head_list = create_preliminary_headlist(
        config,
        optin_database_s
    )

    # create & read optin_database_t
    optin_database_t = config.opt_in_db.optin_db_class(
        config.opt_in_db
    )
    # optin_database_t.load("loadlocation_t")

    head_list = estimate_optin_probabilities(
        preliminary_head_list,
        optin_database_t
    )

    # create and load client database
    client_database = config.client_db.client_db_class(
        config.client_db
    )

    head_list = estimate_client_probabilities(
        config,
        head_list,
        client_database
    )
