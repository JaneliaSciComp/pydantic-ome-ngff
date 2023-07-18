from __future__ import annotations
from pydantic_ome_ngff.latest.base import version
import pydantic_ome_ngff.v04.axes as axv04


class Axis(axv04.Axis):
    """
    Axis metadata.
    See https://ngff.openmicroscopy.org/latest/#axes-md
    """

    _version = version
