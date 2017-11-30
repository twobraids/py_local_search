#!/usr/bin/env python3

from configman import (
    Namespace,
    configuration
)

import json
from collections import defaultdict
from random import shuffle

required_config = Namespace()

required_config.add_option(
    "max_records_per_user",
    default=1,
    doc="how many records per user to include"
)
required_config.add_option(
    "optin_percentage",
    default=0.05,
    doc="percentage of the input file for the optin users"
)
required_config.add_aggregation(
    "client_percentage",
    lambda config, local_config, arg: 1.0 - config.optin_percentage
)
required_config.add_option(
    "optin_s_percentage",
    default=0.95,
    doc="percentage of the optin users in the S group"
)
required_config.add_aggregation(
    "optin_t_percentage",
    lambda config, local_config, arg: 1.0 - config.optin_s_percentage
)
required_config.add_option(
    "data_source_filename",
    default="./aol.json",
    doc="the pathname for the input file"
)
required_config.add_option(
    "temp_data_filename",
    default="./temp.json",
    doc="the pathname for a temporary file"
)
required_config.add_option(
    "optin_s_output_file_name",
    default="optin_s.data.json",
    doc="the pathname for the output optin_s file"
)
required_config.add_option(
    "optin_t_output_file_name",
    default="optin_t.data.json",
    doc="the pathname for the output optin_t file"
)
required_config.add_option(
    "client_output_file_name",
    default="client.data.json",
    doc="the pathname for the output client file"
)
#required_config.add_option(
    #"include_stats",
    #default=False,
    #doc="output stats on common queries"
#)

config = configuration(
    definition_source=required_config,
)

print("reading {}".format(config.data_source_filename))

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

all_data = defaultdict(list)
all_data_size = 0
with open(config.data_source_filename, encoding='utf-8') as f:
    for j in f:
        values = json.loads(j)
        try:
            all_data[values['clientId']].append(
                (values['query'], values['url'])
            )
            all_data_size += 1
            if values['query'] in focused_queries:
                focused_queries[values['query']] += 1
            else:
                focused_queries['*'] += 1

        except KeyError as k:
            print("missing key {}".format(k))

print('number of unique users: {}'.format(len(all_data.keys())))
print('focused queries:')
for key, value in focused_queries.items():
    print('  {}: {} {}'.format(key, value, float(value) / float(all_data_size)))

print('writing {}'.format(config.temp_data_filename))
with open(config.temp_data_filename, encoding='utf-8', mode="w") as o:
    for user in all_data.keys():
        shuffle(all_data[user])
        #print('---------->> {}'.format(all_data[user][:config.max_records_per_user][0]))
        o.write("{}\n".format(json.dumps(all_data[user][:config.max_records_per_user][0])))

print('reading {}'.format(config.temp_data_filename))

all_pairs = []
with open(config.temp_data_filename, encoding='utf-8') as f:
    for raw_record in f:
        #print('|{}|'.format(raw_record))
        all_pairs.append(json.loads(raw_record.strip()))

print('shuffling data')

shuffle(all_pairs)

length = len(all_pairs)

total_optin = int(length * config.optin_percentage)
optin_s_size = int(total_optin * config.optin_s_percentage)
optin_t_size = int(total_optin * config.optin_t_percentage)
client_size = int(length * config.client_percentage)

print('optin_s_size:{}  0:{}'.format(optin_s_size, optin_s_size))
print('optin_t_size:{}  {}:{}'.format(optin_t_size, optin_s_size + 1, optin_s_size + 1 + optin_t_size))
print('client_size:{}  {}:{}'.format(client_size, total_optin + 1, total_optin + 1 + client_size))

print('writing {}'.format(config.optin_s_output_file_name))
optin_s = all_pairs[:optin_s_size]
with open(config.optin_s_output_file_name, encoding='utf-8', mode="w") as o:
    for record in optin_s:
        o.write("{}\n".format(json.dumps(record)))

print('writing {}'.format(config.optin_t_output_file_name))
optin_t = all_pairs[optin_s_size + 1: optin_s_size + 1 + optin_t_size]
with open(config.optin_t_output_file_name, encoding='utf-8', mode="w") as o:
    for record in optin_t:
        o.write("{}\n".format(json.dumps(record)))

print('writing {}'.format(config.client_output_file_name))
client = all_pairs[total_optin + 1:]
with open(config.client_output_file_name, encoding='utf-8', mode="w") as o:
    for record in client:
        o.write("{}\n".format(json.dumps(record)))
