from __future__ import annotations

from pydantic_ome_ngff.latest.base import version
from pydantic_ome_ngff.v04.label import ImageLabel as ImageLabelV04


class ImageLabel(ImageLabelV04):
    """
    image-label metadata.
    See https://ngff.openmicroscopy.org/latest/#label-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: str | None = version
