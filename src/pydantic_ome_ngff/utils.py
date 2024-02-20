from __future__ import annotations
from typing import TYPE_CHECKING, runtime_checkable
from collections import Counter
from typing import Protocol
import numpy as np

if TYPE_CHECKING:
    from typing import Dict, Iterable, Hashable, Tuple, Any

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


def flatten_node(
    node: ArraySpec | GroupSpec, path: str = "/"
) -> Dict[str, ArraySpec | GroupSpec]:
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
    path: `str`, default is 'root'
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


ArraySpec.model_dump


def unflatten_node(
    tree: Dict[str, ArraySpec | GroupSpec], attributes: Dict[str, Any] = {}
) -> ArraySpec | GroupSpec:
    member_lobby = {}
    tree_mut: Dict[str, Dict[str, ArraySpec | GroupSpec]] = {}
    for key, value in tree.items():
        key_parts = key.split("/")
        if key_parts[0] != "":
            raise ValueError(f'Invalid path: {key} does not start with "/".')
        if len(key_parts) == 2:
            member_lobby[key_parts[1]] = value
        else:
            subparent = key_parts[1]
            if subparent not in tree_mut:
                tree_mut[subparent] = {}
            tree_mut[subparent]["/".join(["", *key_parts[2:]])] = value
    for subparent, subchildren in tree_mut.items():
        if subparent in member_lobby:
            if isinstance(member_lobby[subparent], ArraySpec):
                msg = f"Invalid tree: the node named {subparent} is declared both as ArraySpec and GroupSpec"
                raise ValueError(msg)
            else:
                member_lobby[subparent] = unflatten_node(
                    subchildren, attributes=member_lobby[subparent].attributes
                )
        else:
            member_lobby[subparent] = unflatten_node(subchildren)
    return GroupSpec(members=member_lobby, attributes=attributes)


@runtime_checkable
class ArrayLike(Protocol):
    shape: Tuple[int, ...]
    dtype: np.dtype[Any]


@runtime_checkable
class ChunkedArrayLike(ArrayLike, Protocol):
    chunks: Tuple[int, ...]
