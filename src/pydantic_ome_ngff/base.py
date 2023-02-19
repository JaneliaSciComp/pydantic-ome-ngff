from pydantic import BaseModel, Field
from typing import List, Literal, Tuple, Union


NodeType = Literal["array", "group"]


class StrictBaseModel(BaseModel):
    """
    A pydantic basemodel that prevents extra fields.
    """

    class Config:
        extra = "forbid"


class Attrs(BaseModel):
    class Config:
        extra = "allow"


class Node(StrictBaseModel):
    node_type: NodeType
    name: str
    attrs: Attrs = Attrs()


class Array(Node):
    node_type: NodeType = Field("array", const=True)
    shape: Tuple[int, ...]
    dtype: str


class Group(Node):
    node_type: NodeType = Field("group", const=True)
    children: List[Union["Group", Array]]
