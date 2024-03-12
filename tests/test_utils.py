from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from typing import Any, List

from pydantic_ome_ngff.utils import duplicates, listify_numpy
import pytest


@pytest.mark.parametrize(
    "data", [[0], [0, 1, 1, 1, 2], ["a", "a", "b", "b", "c", "c", "d"]]
)
def test_duplicates(data: List[Any]) -> None:
    dupes = duplicates(data)
    for key, value in dupes.items():
        assert data.count(key) == value
        assert value > 1


@pytest.mark.parametrize("data", [np.arange(100), "100", np.dtype("int"), (0, 1, 2, 3)])
def test_listify_numpy(data) -> None:
    observed = listify_numpy(data)
    if isinstance(data, np.ndarray):
        assert observed == data.tolist()
    else:
        assert observed == data
