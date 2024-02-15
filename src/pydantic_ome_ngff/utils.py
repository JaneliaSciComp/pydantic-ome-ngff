from __future__ import annotations
from typing import TYPE_CHECKING, runtime_checkable
from collections import Counter
from typing import Protocol
import numpy as np

if TYPE_CHECKING:
    from typing import Dict, Iterable, Hashable, Tuple

from pydantic_zarr.v2 import GroupSpec, ArraySpec
import os

def duplicates(values: Iterable[Hashable]) -> Dict[Hashable, int]:
    """
    Takes a sequence of hashable elements and returns a dict where the keys are the
    elements of the input that occurred at least once, and the values are the
    frequencies of those elements.
    """
    counts = Counter(values)
    return {k: v for k, v in counts.items() if v > 1}


def flatten_node(node: ArraySpec | GroupSpec, path: str = '/') -> Dict[str, ArraySpec | GroupSpec]:
    """
    Flatten a `GroupSpec` or `ArraySpec`.
    Takes a `GroupSpec` or `ArraySpec` and a string, and returns dictionary with string keys and values that are 
    `GroupSpec` or `ArraySpec`. If the input is an `ArraySpec`, then this function just returns the dict `{path: node}`.
    If the input is a `GroupSpec`, then the resulting dictionary will contain a copy of the input with an empty `members` attribute 
    under the key `path`, as well as copies of the result of calling `flatten_node` on each member of the input, each under a key created by joining `path` with a '/` character
    to the name of each member.

    Paramters
    ---------
    node: `GroupSpec` | `ArraySpec`
        The node to flatten.
    path: `str`, default is '/'
        The root path. If the input is a `GroupSpec`, then the keys in `GroupSpec.members` will be 
        made relative to `path` when used as keys in the result dictionary.

    Returns
    -------
    `Dict[str, GroupSpec | ArraySpec]`

    """
    result = {}
    if isinstance(node, ArraySpec):
        model_copy = node.model_copy(deep=True)

    else:
        model_copy = node.model_copy(update={"members": {}})
        for name, value in node.members.items():
            result.update(flatten_node(value, os.path.join(path, name)))

    result[path] = model_copy
        
    return result

@runtime_checkable
class ArrayLike(Protocol):
    shape: Tuple[int, ...]
    dtype: np.dtype

@runtime_checkable
class ChunkedArrayLike(ArrayLike, Protocol):
    chunks: Tuple[int, ...]