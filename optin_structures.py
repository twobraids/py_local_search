from blender.sorted_dict_of_lists import (
    SortedDictOfLists
)

from math import (
    log as ln,
    exp
)
from numpy.random import (
    laplace
)

from configman import (
    Namespace
)

from blender.in_memory_structures import (
    URLCounter,
    URLStatsMapping,
    QueryURLMapping
)


# --------------------------------------------------------------------------------------------------------
# 3rd Level Structures
#     Contains a single url's stats
#     see constructor for attributes

# --------------------------------------------------------------------------------------------------------
# 2nd Level Structures
#     Contains a single query's stats and urls
#     Mapping
#         urls are the key
#         3rd Level structures as the value


# --------------------------------------------------------------------------------------------------------
# Top Level Structures -
#    Mapping
#        queries serve as the key
#        2nd Level structures as the value

