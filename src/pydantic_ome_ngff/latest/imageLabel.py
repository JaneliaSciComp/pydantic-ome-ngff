from pydantic_ome_ngff.v04.imageLabel import ImageLabel as ImageLabelV04
from pydantic_ome_ngff.latest.base import version
from typing import Optional


class ImageLabel(ImageLabelV04):
    """
    image-label metadata.
    See https://ngff.openmicroscopy.org/latest/#label-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: Optional[str] = version
