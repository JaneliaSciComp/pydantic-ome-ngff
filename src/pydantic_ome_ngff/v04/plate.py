from __future__ import annotations

from pydantic import (
    BaseModel,
    NonNegativeInt,
    PositiveInt,
    ValidationError,
    field_validator,
)
from pydantic_zarr.v2 import ArraySpec, GroupSpec

from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.well import WellGroup


class Acquisition(BaseModel):
    id: PositiveInt
    name: str | None = None
    maximumfieldcount: PositiveInt


class Entry(BaseModel):
    name: str


class WellMetadata(BaseModel):
    # must be {rowName}/{columnName}
    path: str
    rowIndex: NonNegativeInt
    columnIndex: NonNegativeInt


class PlateMetadata(VersionedBase):
    """
    Plate metadata
    see https://ngff.openmicroscopy.org/0.4/#plate-md
    """

    # the version here as a private class attribute because the version is not required by the spec
    _version = version
    version: str | None = version
    name: str | None = None
    acquisitions: tuple[Acquisition, ...]
    columns: tuple[Entry, ...]
    rows: tuple[Entry, ...]
    field_count: PositiveInt
    wells: tuple[WellMetadata, ...]


class GroupAttrs(BaseModel):
    plate: PlateMetadata


class Group(GroupSpec[GroupAttrs, WellGroup | GroupSpec | ArraySpec]):
    @field_validator("members", mode="after")
    @classmethod
    def contains_well_group(
        cls, members: WellGroup | GroupSpec | ArraySpec
    ) -> WellGroup | GroupSpec | ArraySpec:
        """
        Check that .members contains a WellGroup
        """
        if not any(isinstance(v, WellGroup) for v in members.values()):
            raise ValidationError
        return members
