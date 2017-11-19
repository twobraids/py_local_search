from unittest import TestCase
from mock import (
    MagicMock,
    patch
)
from collections import (
    Mapping
)
from configman.dotdict import (
    DotDict,
    DotDictWithAcquisition
)

from blender.head_list import (
    HeadList,
    HeadListQuery,
)
from blender.in_memory_structures import (
    URLStats,
    Query,
    QueryCollection
)
from blender.main import (
    create_preliminary_headlist,
    estimate_optin_probabilities
)


