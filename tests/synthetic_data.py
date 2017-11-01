from functools import partial

def load_synthetic_data_set(data_set, db):
    for q, u, c in data_set:
        for i in range(c):
            db.add((q, u))
    return db

minimal_constants = {
    "epsilon": 1.0,
    "delta": 0.000001,
    "m_o": 1,
    "head_list_db.m": 100,
}

standard_constants = {
    "epsilon": 4.0,
    "delta": 0.000001,
    "m_o": 10,
    "head_list_db.m": 5,
}

single_set = [
    ('q1', 'q1u1', 100),
    ('q2', 'q2u1', 100)
]
load_single_data = partial(load_synthetic_data_set, single_set)

tiny_set = [
    ('q1', 'q1u1', 10),
    ('q2', 'q2u1', 10),
    ('q2', 'q2u2', 20),
    ('q3', 'q3u1', 30),
    ('q4', 'q4u1', 99),
    ('q4', 'q4u2', 99),
    ('q5', 'q5u1', 10),
    ('q5', 'q5u2', 20),
    ('q6', 'q6u1', 99),
    ('q6', 'q6u2', 10),
    ('q7', 'q7u1', 99),
    ('q7', 'q7u2', 99),
]
load_tiny_data = partial(load_synthetic_data_set, tiny_set)

small_set = [
    ('q1', 'q1u1', 10),
    ('q2', 'q2u1', 10),
    ('q2', 'q2u2', 20),
    ('q3', 'q3u1', 30),
    ('q4', 'q4u1', 100),
    ('q4', 'q4u2', 100),
    ('q5', 'q5u1', 10),
    ('q5', 'q5u2', 20),
    ('q6', 'q6u1', 100),
    ('q6', 'q6u2', 10),
    ('q7', 'q7u1', 100),
    ('q7', 'q7u2', 100),
    ('q8', 'q8u1', 50),
    ('q8', 'q8u2', 50),
    ('q8', 'q8u3', 50),
    ('q8', 'q8u4', 50),
    ('q8', 'q8u5', 50),
    ('q8', 'q8u6', 50),
    ('q8', 'q8u7', 45),
    ('q8', 'q8u8', 45),
]
load_small_data = partial(load_synthetic_data_set, small_set)

