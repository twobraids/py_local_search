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
    HeadListURLStatsMapping,
)
from blender.in_memory_structures import (
    URLCounter,
    URLStatsMapping,
    QueryURLMapping
)
from blender.main import (
    create_preliminary_headlist,
    estimate_optin_probabilities
)


