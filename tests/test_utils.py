from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, List

from pydantic_ome_ngff.utils import duplicates
import pytest


@pytest.mark.parametrize(
    "data", [[0], [0, 1, 1, 1, 2], ["a", "a", "b", "b", "c", "c", "d"]]
)
def test_duplicates(data: List[Any]) -> None:
    dupes = duplicates(data)
    for key, value in dupes.items():
        assert data.count(key) == value
        assert value > 1
