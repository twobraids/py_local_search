from configman import (
    configuration,
    Namespace,
    RequiredConfig,
    class_converter,
)


# define the constants used for the Blender algorithm as well as the classes for dependency injection

required_config = Namespace()

required_config.namespace('opt_in_db')
required_config.opt_in_db.add_option(
    name="optin_db_class",
    default="optin_structures.QueryURLMappingClass",
    from_string_converter=class_converter,
    doc="dependency injection of a class to serve as non-headlist <q, u> databases"
)

required_config.namespace('head_list_db')
required_config.head_list_db.add_option(
    name="headlist_class",
    default="optin_structures.HeadList",
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
def estimate_optin_probabilities(config, preliminary_head_list, optin_database_t):
    """
    Parameters:
        config -
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


