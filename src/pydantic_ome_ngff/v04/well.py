from __future__ import annotations

from typing import Union
from pydantic import BaseModel, ValidationError, field_validator
from pydantic_zarr.v2 import ArraySpec, GroupSpec

from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.v04 import multiscale
from pydantic_ome_ngff.v04.base import version


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
    images: tuple[Image, ...]


class GroupAttrs(BaseModel):
    well: WellMetadata


class Group(GroupSpec[GroupAttrs, Union[multiscale.Group, GroupSpec, ArraySpec]]):
    @field_validator("members", mode="after")
    @classmethod
    def contains_multiscale_group(
        cls, members: Group | GroupSpec | ArraySpec
    ) -> Group | GroupSpec | ArraySpec:
        """
        Check that .members contains a MultiscaleGroup
        """
        if not any(isinstance(v, multiscale.Group) for v in members.values()):
            raise ValidationError
        return members
