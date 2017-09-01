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
    default=10,
    doc="maximum number of records per opt-in user",
)


# direct implementations of the Blender algorithms

# CreateHeadList from Figure 3
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

    return preliminary_head_list


# EstimateClientProbabilities
def estimate_client_probabilities(config, client_database):
    pass

