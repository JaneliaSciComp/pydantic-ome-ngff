from typing import List, Optional

from pydantic import BaseModel, PositiveInt
from pydantic_ome_ngff.base import VersionedBase

from pydantic_ome_ngff.v04.base import version


class Acquisition(BaseModel):
    id: PositiveInt
    name: Optional[str]
    maximumfieldcount: PositiveInt


class Entry(BaseModel):
    name: str


class Well(BaseModel):
    # must be {rowName}/{columnName}
    path: str
    rowIndex: PositiveInt
    columnIndex: PositiveInt


class Plate(VersionedBase):
    """
    Plate metadata
    see https://ngff.openmicroscopy.org/0.4/#plate-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: Optional[str] = version
    name: Optional[str]
    acquisitions: List[Acquisition]
    columns: List[Entry]
    rows: List[Entry]
    field_count: PositiveInt
    wells: List[Well]
