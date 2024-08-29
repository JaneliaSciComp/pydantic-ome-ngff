from __future__ import annotations

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_zarr.v2 import ArraySpec, GroupSpec

from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.multiscale import MultiscaleGroup


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


class WellGroupAttrs(BaseModel):
    well: WellMetadata


class WellGroup(GroupSpec[WellGroupAttrs, MultiscaleGroup | GroupSpec | ArraySpec]):
    @field_validator("members", mode="after")
    @classmethod
    def contains_multiscale_group(
        cls, members: MultiscaleGroup | GroupSpec | ArraySpec
    ) -> MultiscaleGroup | GroupSpec | ArraySpec:
        """
        Check that .members contains a MultiscaleGroup
        """
        if not any(isinstance(v, MultiscaleGroup) for v in members.values()):
            raise ValidationError
        return members
