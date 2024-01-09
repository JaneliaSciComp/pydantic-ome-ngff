from __future__ import annotations
from typing import Optional


from pydantic_ome_ngff.latest.base import version
from pydantic_ome_ngff.v04.plate import PlateMetadata as PlateMetaV04


class PlateMeta(PlateMetaV04):
    """
    Plate metadata.
    See https://ngff.openmicroscopy.org/latest/#plate-md
    """

    _version = version
    version: Optional[str] = version
