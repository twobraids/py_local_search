#!/usr/bin/env python3

import json
from collections import defaultdict

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

all_data_keyed_clientid = defaultdict(list)
number_of_query_url_pairs = 0
with open('aol.json', encoding='utf-8') as f:
    for client_query_url_json_str in f:
        client_query_url_tuple = json.loads(client_query_url_json_str)
        client_id = client_query_url_tuple['clientId']
        query_str = client_query_url_tuple['query']
        url_str = client_query_url_tuple['url']
        all_data_keyed_clientid[client_id].append((query_str, url_str))
        number_of_query_url_pairs += 1
        if query_str in focused_queries:
            focused_queries[query_str] += 1
        else:
            focused_queries['*'] += 1

print('number of unique users: {}'.format(len(all_data_keyed_clientid.keys())))
print('focused queries:')
for key, value in focused_queries.items():
    print('  {}: {} {}'.format(key, value, float(value) / float(number_of_query_url_pairs)))
