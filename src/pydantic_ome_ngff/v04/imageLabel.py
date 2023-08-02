from __future__ import annotations
import warnings
from typing import List, Optional, Tuple
import textwrap
from pydantic import BaseModel, Field, validator
from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.v04.base import version


class Color(BaseModel):
    label_value: int = Field(..., alias="label-value")
    rgba: Optional[Tuple[int, int, int, int]]


class Source(BaseModel):
    image: Optional[str] = "../../"


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
    version: Optional[str] = version
    colors: Optional[List[Color]]
    properties: Optional[List[Properties]]
    source: Optional[Source]

    @validator("version")
    def check_version(cls, ver: str) -> str:
        if ver is None:
            msg = f"""
            The field "version" is "None". Version {cls._version} of
            the OME-NGFF spec states that "version" must either be unset or the string
            "{cls._version}"
            """
            warnings.warn(textwrap.fill(msg))
        return ver

    @validator("colors")
    def check_colors(cls, colors: Optional[List[Color]]) -> Optional[List[Color]]:
        if colors is None:
            msg = f"""
            The field "colors" is "None". Version {cls._version} of
            the OME-NGFF spec states that "colors" should be a list of label
            descriptors.
            """
            warnings.warn(textwrap.fill(msg))
        else:
            dupes = duplicates(x.label_value for x in colors)
            if len(dupes) > 1:
                msg = f"""
                    Duplicated label-value: {tuple(dupes.keys())}.
                    label-values must be unique across elements of `colors`
                    """
                raise ValueError(textwrap.fill(msg))

        return colors
