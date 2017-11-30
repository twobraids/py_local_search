from math import (
    exp
)

from numpy.random import (
    random,
    choice,
)

def local_alg(config, head_list, local_query_url_iter):
    """to be used in testing as in production, it will be executed by the client.  It should, therefore,
    be written in Javascript or, even better, Rust"""
    tau = (
        (exp(config.epsilon_prime_q) + (config.delta_prime_q / 2.0) * (head_list.number_of_query_url_pairs - 1))
        /
        (exp(config.epsilon_prime_q) + head_list.number_of_query_url_pairs - 1)
    )
    for a_query, a_url in local_query_url_iter():
        if a_query not in head_list:
            a_query = '*'
        if a_url not in head_list[a_query]:
            a_url = '*'

        if random() <= (1 - tau):
            # there is confusion on the significance of a database structure has only unqiue <q, u> pairs
            # or duplicates.  Some code clearly allows duplicates.  the definiton of |D| is for unique or
            # with duplicates?
            alt_query = choice(list(head_list.keys()))
            alt_url = choice(list(head_list[alt_query].keys()))
            yield alt_query, alt_url
            continue

        if random() <= (1 - head_list[a_query].tau):
            alt_url = choice(list(head_list[a_query].keys()))
            yield a_query, alt_url
            continue

        yield a_query, a_url
