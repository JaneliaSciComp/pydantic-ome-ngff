from __future__ import annotations
from typing import List

from pydantic import BaseModel
from pydantic_ome_ngff.base import VersionedBase

from pydantic_ome_ngff.v04.base import version


class Image(BaseModel):
    path: str
    acquisition: int | None


class Well(VersionedBase):
    """
    Well metadata.
    See https://ngff.openmicroscopy.org/0.4/#well-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: str | None = version
    images: List[Image]
