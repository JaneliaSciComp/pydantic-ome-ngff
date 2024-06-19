from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from zarr.storage import BaseStore

import numpy as np

if TYPE_CHECKING:
    from typing import Any, Hashable, Iterable


def duplicates(values: Iterable[Hashable]) -> dict[Hashable, int]:
    """
    Takes a sequence of hashable elements and returns a dict where the keys are the
    elements of the input that occurred at least once, and the values are the
    frequencies of those elements.
    """
    counts = Counter(values)
    return {k: v for k, v in counts.items() if v > 1}


@runtime_checkable
class ArrayLike(Protocol):
    shape: tuple[int, ...]
    dtype: np.dtype[Any]


@runtime_checkable
class ChunkedArrayLike(ArrayLike, Protocol):
    chunks: tuple[int, ...]


def listify_numpy(data: Any) -> Any:
    """
    If the input is a numpy array, turn it into a list and return it.
    Otherwise return the input unchanged.
    """
    if isinstance(data, np.ndarray):
        return data.tolist()
    return data


def get_path(store: BaseStore) -> str:
    """
    Get a path from a zarr store
    """
    if hasattr(store, "path"):
        return store.path

    else:
        return ""
