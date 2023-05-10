from __future__ import annotations
import warnings
from typing import List, Tuple

from pydantic import BaseModel, Field, validator
from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.utils import duplicates

from pydantic_ome_ngff.v04.base import version


class Color(BaseModel):
    label_value: int = Field(..., alias="label-value")
    rgba: Tuple[int, int, int, int] | None


class Source(BaseModel):
    image: str | None = "../../"


class Properties(BaseModel):
    label_value: int = Field(..., alias="label-value")


class ImageLabel(VersionedBase):
    """
    image-label metadata.
    See https://ngff.openmicroscopy.org/0.4/#label-md
    """

    # we need to put the version here as a private class attribute because the version
    # field is not required by the spec...
    _version = version

    # SPEC: version is either unset or a string?
    version: str | None = version
    colors: List[Color] | None
    properties: Properties | None
    source: Source | None

    @validator("version")
    def check_version(cls, ver: str) -> str:
        if ver is None:
            msg = f"""
            The field "version" is "None". Version {cls._version} of
            the OME-NGFF spec states that "version" must either be unset or the string
            "{cls._version}"
            """
            warnings.warn(msg)
        return ver

    @validator("colors")
    def check_colors(cls, colors: List[Color] | None) -> List[Color] | None:
        if colors is None:
            msg = f"""
            The field "colors" is "None". Version {cls._version} of
            the OME-NGFF spec states that "colors" should be a list of label 
            descriptors.
            """
            warnings.warn(msg)
        else:
            dupes = duplicates(x.label_value for x in colors)
            if len(dupes) > 1:
                msg = f"""
                    Duplicated label-value: {tuple(dupes.keys())}.
                    label-values must be unique across elements of `colors`
                    """
                raise ValueError(msg)

        return colors
