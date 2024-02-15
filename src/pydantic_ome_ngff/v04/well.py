from __future__ import annotations
from typing import List, Union

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_zarr.v2 import ArraySpec, GroupSpec

from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.v04.base import version
import pydantic_ome_ngff.v04.multiscales as multiscales


class Image(BaseModel):
    path: str
    acquisition: int | None


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
    def contains_multiscale_group(
        cls, members: Union[Group, GroupSpec, ArraySpec]
    ) -> Union[Group, GroupSpec, ArraySpec]:
        """
        Check that .members contains a MultiscaleGroup
        """
        if not any(map(lambda v: isinstance(v, multiscales.Group), members.values())):
            raise ValidationError
        return members
