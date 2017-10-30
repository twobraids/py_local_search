import json
from collections import defaultdict
from random import shuffle

m = 1

print("reading aol.json")

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
with open("aol.json", encoding='utf-8') as f:
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

print ('number of unique users: {}'.format(len(all_data.keys())))
print ('focused queries:')
for key, value in focused_queries.items():
    print ('  {}: {} {}'.format(key, value, float(value) / float(all_data_size)))

print('writing aol.data')
with open("aol.data", encoding='utf-8', mode="w") as o:
    for user in all_data.keys():
        shuffle(all_data[user])
        o.write("{}\n".format(json.dumps(all_data[user][:m])))

print('reading aol.data')

all_pairs = []
with open("aol.data", encoding='utf-8') as f:
    for raw_record in f:
        #print('|{}|'.format(raw_record))
        all_pairs.append(json.loads(raw_record.strip()))

print('shuffling data')

shuffle(all_pairs)

length = len(all_pairs)

total_optin = int(length * 0.05)
optin_s_size = int(total_optin * 0.95)
optin_t_size = int(total_optin * 0.05)
client_size = int(length * 0.95)

print('optin_s_size:{}  0:{}'.format(optin_s_size, optin_s_size))
print('optin_t_size:{}  {}:{}'.format(optin_t_size, optin_s_size + 1, optin_s_size + 1 + optin_t_size))
print('client_size:{}  {}:{}'.format(client_size, total_optin + 1, total_optin + 1 + client_size))

print('writing optin_s')
optin_s = all_pairs[:optin_s_size]
with open('optin_s.data', encoding='utf-8', mode="w") as o:
    for record in optin_s:
        o.write("{}\n".format(json.dumps(record)))

print('writing optin_t')
optin_t = all_pairs[optin_s_size + 1: optin_s_size + 1 + optin_t_size]
with open('optin_t.data', encoding='utf-8', mode="w") as o:
    for record in optin_t:
        o.write("{}\n".format(json.dumps(record)))

print('writing client')
client = all_pairs[total_optin + 1:]
with open('client.data', encoding='utf-8', mode="w") as o:
    for record in client:
        o.write("{}\n".format(json.dumps(record)))



