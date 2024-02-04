from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, PositiveInt, ValidationError, field_validator
from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_zarr.v2 import GroupSpec, ArraySpec
from typing import Union

import pydantic_ome_ngff.v04.well as well


class Acquisition(BaseModel):
    id: PositiveInt
    name: Optional[str] = None
    maximumfieldcount: PositiveInt


class Entry(BaseModel):
    name: str


class WellMetadata(BaseModel):
    # must be {rowName}/{columnName}
    path: str
    rowIndex: PositiveInt
    columnIndex: PositiveInt


class PlateMetadata(VersionedBase):
    """
    Plate metadata
    see https://ngff.openmicroscopy.org/0.4/#plate-md
    """

    # the version here as a private class attribute because the version is not required by the spec
    _version = version
    version: str | None = version
    name: str | None = None
    acquisitions: List[Acquisition]
    columns: List[Entry]
    rows: List[Entry]
    field_count: PositiveInt
    wells: List[WellMetadata]


class GroupAttrs(BaseModel):
    plate: PlateMetadata


class Group(GroupSpec[GroupAttrs, Union[well.Group, GroupSpec, ArraySpec]]):
    @field_validator("members", mode="after")
    @classmethod
    def contains_well_group(
        cls, members: Union[Group, GroupSpec, ArraySpec]
    ) -> Union[Group, GroupSpec, ArraySpec]:
        """
        Check that .members contains a WellGroup
        """
        if not any(map(lambda v: isinstance(v, well.Group), members.values())):
            raise ValidationError
        return members
