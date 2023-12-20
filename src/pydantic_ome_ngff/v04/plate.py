from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, PositiveInt, ValidationError, field_validator
from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_zarr.v2 import GroupSpec, ArraySpec
from typing import Union

from pydantic_ome_ngff.v04.well import WellGroup


class Acquisition(BaseModel):
    id: PositiveInt
    name: Optional[str] = None
    maximumfieldcount: PositiveInt


class Entry(BaseModel):
    name: str


class WellMeta(BaseModel):
    # must be {rowName}/{columnName}
    path: str
    rowIndex: NonNegativeInt
    columnIndex: NonNegativeInt


class PlateMeta(VersionedBase):
    """
    Plate metadata
    see https://ngff.openmicroscopy.org/0.4/#plate-md
    """

    # the version here as a private class attribute because the version is not required by the spec
    _version = version
    version: Optional[str] = version
    name: Optional[str] = None
    acquisitions: List[Acquisition]
    columns: List[Entry]
    rows: List[Entry]
    field_count: PositiveInt
    wells: List[WellMeta]


class PlateAttributes(BaseModel):
    plate: PlateMeta


class PlateGroup(GroupSpec[PlateAttributes, Union[WellGroup, GroupSpec, ArraySpec]]):
    @field_validator("members", mode="after")
    @classmethod
    def contains_well(
        cls, members: Union[WellGroup, GroupSpec, ArraySpec]
    ) -> Union[WellGroup, GroupSpec, ArraySpec]:
        """
        Check that .members contains a WellGroup
        """
        if not any(map(lambda v: isinstance(v, WellGroup), members.values())):
            raise ValidationError
        return members
