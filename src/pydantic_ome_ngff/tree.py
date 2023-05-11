from __future__ import annotations
from typing import (
    Protocol,
    Tuple,
    Dict,
    Any,
    Iterable,
    Literal,
    List,
    Union,
    runtime_checkable,
)
from pydantic import BaseModel, Field
from pydantic_ome_ngff.base import StrictBase

NodeType = Literal["array", "group"]


class Attrs(BaseModel):
    ...


class Node(StrictBase):
    node_type: NodeType
    name: str
    attrs: Attrs = Attrs()


class Array(Node):
    node_type: NodeType = Field("array", const=True)
    shape: Tuple[int, ...]
    dtype: str


class Group(Node):
    node_type: NodeType = Field("group", const=True)
    children: List[Union[Group, Array]]


class NodeLike(Protocol):
    basename: str
    attrs: Dict[str, Any]


@runtime_checkable
class ArrayLike(NodeLike, Protocol):
    shape: Tuple[int, ...]
    dtype: Any


@runtime_checkable
class GroupLike(NodeLike, Protocol):
    def values(self) -> Iterable[Union[GroupLike, ArrayLike]]:
        """
        Iterable of the children of this group
        """
        ...


def build_tree(element: Union[GroupLike, ArrayLike]) -> Union[Group, Array]:
    """
    Recursively parse an array-like or group-like into an Array or Group.
    """
    result: Union[Group, Array]
    name = element.basename
    attrs = Attrs(**element.attrs)

    if isinstance(element, ArrayLike):
        result = Array(
            shape=element.shape, name=name, dtype=str(element.dtype), attrs=attrs
        )
    elif isinstance(element, GroupLike):
        children = list(map(build_tree, element.values()))
        result = Group(name=name, attrs=attrs, children=children)
    else:
        msg = f"Object of type {type(element)} cannot be processed."
        raise ValueError(msg)
    return result
