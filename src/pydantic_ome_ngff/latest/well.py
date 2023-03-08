from typing import Optional
from pydantic_ome_ngff.latest.base import version
from pydantic_ome_ngff.v04.well import Well as WellV04


class Well(WellV04):
    """
    Well metadata.
    See https://ngff.openmicroscopy.org/latest/#well-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: Optional[str] = version
