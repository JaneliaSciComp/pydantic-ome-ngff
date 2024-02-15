from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any, List

from pydantic_ome_ngff.utils import duplicates, flatten_node
from pydantic_zarr.v2 import ArraySpec, GroupSpec
import numpy as np
import pytest

def test_flatten_node() -> None:
    a = ArraySpec.from_array(np.arange(10))
    flattened = flatten_node(a)
    assert flattened == {'/': a}

    b = GroupSpec(attributes={'foo': 10}, members={'name': a})
    flattened_b = flatten_node(b)
    assert flattened_b['/'] == b.model_copy(update={"members": {}})
    assert flattened_b['/name'] == a

    c = GroupSpec(attributes={}, members={'b': b, 'a': a})
    flattened_c = flatten_node(c, path='c')
    assert flattened_c['c'] == c.model_copy(update={"members": {}})
    assert flattened_c["c/b"] == b.model_copy(update={"members": {}})
    assert flattened_c["c/a"] == a
    assert flattened_c["c/b/name"] == a

@pytest.mark.parametrize('data', [[0], [0,1,1,1,2], ['a','a','b','b','c','c','d']])
def test_duplicates(data: List[Any]) -> None:
    dupes = duplicates(data)
    for key, value in dupes.items():
        assert data.count(key) == value
        assert value > 1