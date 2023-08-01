from __future__ import annotations
from typing import Optional


from pydantic_ome_ngff.latest.base import version
from pydantic_ome_ngff.v04.plate import Plate as PlateV04


class Plate(PlateV04):
    """
    Plate metadata.
    See https://ngff.openmicroscopy.org/latest/#plate-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: Optional[str] = version
