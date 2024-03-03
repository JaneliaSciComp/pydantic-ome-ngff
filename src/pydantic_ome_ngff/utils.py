from __future__ import annotations
from typing import TYPE_CHECKING, runtime_checkable
from collections import Counter
from typing import Protocol
import numpy as np

if TYPE_CHECKING:
    from typing import Dict, Iterable, Hashable, Tuple, Any


def duplicates(values: Iterable[Hashable]) -> Dict[Hashable, int]:
    """
    Takes a sequence of hashable elements and returns a dict where the keys are the
    elements of the input that occurred at least once, and the values are the
    frequencies of those elements.
    """
    counts = Counter(values)
    return {k: v for k, v in counts.items() if v > 1}


@runtime_checkable
class ArrayLike(Protocol):
    shape: Tuple[int, ...]
    dtype: np.dtype[Any]


@runtime_checkable
class ChunkedArrayLike(ArrayLike, Protocol):
    chunks: Tuple[int, ...]
