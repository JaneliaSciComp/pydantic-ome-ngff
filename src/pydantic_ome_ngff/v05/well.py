from typing import List, Optional

from pydantic import BaseModel

from pydantic_ome_ngff.v05 import version as v05_version


class Image(BaseModel):
    path: str
    acquisition: Optional[int]


class Well(BaseModel):
    version: str = v05_version
    images: List[Image]
