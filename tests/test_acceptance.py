from unittest import TestCase

from configman import (
    configuration,
)

from blender.main import (
    default_data_structures,
    required_config,
    create_preliminary_headlist,
    estimate_optin_probabilities
)

standards_from_figure_9 = {
    '*': [0.9108, 0.9103, 0.9199, 0.9100, 0.1468, ],
    'google': [0.0213, 0.0216, 0.0213, 0.0217, 0.0216, ],
    'yahoo': [0.0067, 0.0070, 0.0046, 0.0073, 0.0325,],
    'google.com': [0.0067, 0.0056, 0.0023, 0.0061, 0.0194,],
    'myspace.com': [0.0057, 0.0052, 0.0022, 0.0057, 0.0258,],
    'mapquest': [0.0054, 0.0051, 0.0062, 0.0053, 0.0192,],
    'yahoo.com': [0.0043, 0.0043, 0.0021, 0.0048, 0.0192,],
    'www.google.com': [0.0034, 0.0004, 0.0004, 0.0032, 0.0098,],
    'myspace': [0.0033, 0.0034, 0.0042, 0.0035, 0.0255,],
    'ebay': [0.0028, 0.0026, 0.0028, 0.0028, 0.0254,],
}

aol_pq = 0
blender_pq = 1
optin_pq = 2
optin_sum = 3
client_pq = 4
client_sum = 5

standards_from_analyze_aol = {
    '*': [0, 0.9609944925686271, ],
    'google': [0, 0.013611629573536801, ],
    'yahoo': [0, 0.00552769611162353,],
    'google.com': [0, 0.0027381056655940584,],
    'myspace.com': [0, 0.002800751482347638,],
    'mapquest': [0, 0.002955617290430584,],
    'yahoo.com': [0, 0.003163202279279063,],
    'www.google.com': [0, 0.0013820654696103754,],
    'myspace': [0, 0.003147103641640417,],
    'ebay': [0, 0.0036793359173104023,],
}

acceptance_config = {
    "epsilon": 4,
    "delta": 0.000001,
    "m_o": 1.0,
    "m_c": 1.0,
    "f_c": 0.85,
    "optin_database_s_filename": "tests/optin_s.data.json",
    "optin_database_t_filename": "tests/optin_t.data.json",
    "client_database_filename": "tests/client.data.json",
    "output_filename": "tests/out.data",
}

config = configuration(
    definition_source=required_config,
    values_source_list=[
        # create the overriding hierarchy for the sources of configuration.
        # each source will override values from sources higher in the list
        default_data_structures,
        acceptance_config,
    ]
)


class TestDirectBenderFunctionImplementations(TestCase):
    def testCreationOfHeadList(self):
        optin_database_s = config.optin_db.optin_db_class(config.optin_db)
        optin_database_s.load(config.optin_database_s_filename)
        preliminary_head_list = create_preliminary_headlist(
            config,
            optin_database_s
        )
        optin_database_t = config.optin_db.optin_db_class(config.optin_db)
        optin_database_t.load(config.optin_database_t_filename)
        head_list_with_probabilities = estimate_optin_probabilities(
            preliminary_head_list,
            optin_database_t
        )

        #for query_str in standards_from_figure_9.keys():
        for query_str in standards_from_analyze_aol.keys():
            print ("{} {}: {}".format(query_str, blender_pq, standards_from_analyze_aol[query_str][blender_pq]))
            self.assertAlmostEqual(
                head_list_with_probabilities[query_str].probability,
                standards_from_analyze_aol[query_str][blender_pq],
                3
            )
