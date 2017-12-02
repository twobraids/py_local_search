#!/usr/bin/env python3

import json
from collections import defaultdict
from functools import reduce

from configman import (
    configuration,
    environment,
    ConfigFileFutureProxy as configuration_file,
    command_line
)

from blender.main import (
    required_config,
    default_data_structures,
    create_preliminary_headlist
)

focused_queries = {
    "google": 0,
    "yahoo": 0,
    "google.com": 0,
    "myspace.com": 0,
    "mapquest": 0,
    "yahoo.com": 0,
    "www.google.com": 0,
    "myspace": 0,
    "ebay": 0,
    "*": 0,
}

config = configuration(
    definition_source=required_config,
    values_source_list=[
        default_data_structures,
        environment,
        configuration_file,
        command_line,
    ]

)

# create a headlist so that the * count only includes headlist items
optin_database_s = config.optin_db.optin_db_class(
    config.optin_db
)
optin_database_s.load(config.optin_database_s_filename)
head_list = create_preliminary_headlist(
    config,
    optin_database_s
)

all_data_keyed_by_clientid = defaultdict(list)
number_of_query_url_pairs = 0
number_of_query_url_pairs_in_headlist_but_not_in_focus = 0
with open('aol.json', encoding='utf-8') as f:
    for client_query_url_json_str in f:
        client_query_url_tuple = json.loads(client_query_url_json_str)
        client_id = client_query_url_tuple['clientId']
        query_str = client_query_url_tuple['query']
        url_str = client_query_url_tuple['url']
        all_data_keyed_by_clientid[client_id].append((query_str, url_str))
        number_of_query_url_pairs += 1
        if query_str in focused_queries:
            focused_queries[query_str] += 1
        elif query_str in head_list:
            number_of_query_url_pairs_in_headlist_but_not_in_focus += 1
        else:
            focused_queries['*'] += 1

assert number_of_query_url_pairs == reduce(lambda x, y: x + y, focused_queries.values(), 0) + number_of_query_url_pairs_in_headlist_but_not_in_focus
print('number of unique users: {}'.format(len(all_data_keyed_by_clientid.keys())))
print('number of <query, url> pairs: {}'.format(number_of_query_url_pairs))
print('focused queries:')
for key, value in focused_queries.items():
    print('  {}: {} {}'.format(key, value, float(value) / float(number_of_query_url_pairs)))
