from typing import List, Optional

from pydantic import BaseModel, PositiveInt

from pydantic_ome_ngff.v05 import version as v05_version


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


class Plate(BaseModel):
    name: Optional[str]
    version: Optional[str] = v05_version
    acquisitions: List[Acquisition]
    columns: List[Entry]
    rows: List[Entry]
    field_count: PositiveInt
    wells: List[Well]
