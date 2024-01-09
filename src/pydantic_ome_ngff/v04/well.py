from __future__ import annotations
from typing import List, Optional, Union

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_ome_ngff.base import VersionedBase

from pydantic_ome_ngff.v04.base import version
import pydantic_ome_ngff.v04.multiscales as multiscales
from pydantic_zarr.v2 import GroupSpec, ArraySpec


class Image(BaseModel):
    path: str
    acquisition: Optional[int]


class WellMetadata(VersionedBase):
    """
    Well metadata.
    See https://ngff.openmicroscopy.org/0.4/#well-md
    """

    _version = version
    version: str | None = version
    images: List[Image]


class GroupAttrs(BaseModel):
    well: WellMetadata


class Group(GroupSpec[GroupAttrs, Union[multiscales.Group, GroupSpec, ArraySpec]]):
    @field_validator("members", mode="after")
    @classmethod
    def contains_well(
        cls, members: Union[Group, GroupSpec, ArraySpec]
    ) -> Union[Group, GroupSpec, ArraySpec]:
        """
        Check that .members contains a MultiscaleGroup
        """
        if not any(map(lambda v: isinstance(v, Group), members.values())):
            raise ValidationError
        return members
