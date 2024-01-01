from __future__ import annotations
import warnings
from typing import List, Optional, Tuple, Annotated

from pydantic import BaseModel, Field, field_validator
from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.v04.base import version

ConInt = Annotated[int, Field(strict=True, ge=0, le=255)]
RGBA = Tuple[ConInt, ConInt, ConInt, ConInt]


class Color(BaseModel):
    """
    a label value and RGBA as defined in https://ngff.openmicroscopy.org/0.4/#label-md
    """

    label_value: int = Field(..., serialization_alias="label-value")
    rgba: RGBA | None


class Source(BaseModel):
    image: str | None = "../../"


class Properties(BaseModel):
    label_value: int = Field(..., serialization_alias="label-value")


class ImageLabel(VersionedBase):
    """
    image-label metadata.
    See https://ngff.openmicroscopy.org/0.4/#label-md
    """

    _version = version

    version: Optional[str] = version
    colors: List[Color] | None = None
    properties: Properties | None = None
    source: Source | None = None

    @field_validator("version")
    @classmethod
    def check_version(cls, ver: str | None) -> str:
        if ver is None:
            msg = (
                f"The `version` attribute is `None`. Version {cls._version} of "
                f"the OME-NGFF spec states that `version` must either be unset or the string {cls._version}"
            )
            warnings.warn(msg, stacklevel=1)

        return ver

    @field_validator("colors")
    @classmethod
    def check_colors(cls, colors: Optional[List[Color]]) -> Optional[List[Color]]:
        if colors is None:
            msg = (
                f"The field `colors` is `None`. Version {cls._version} of"
                "the OME-NGFF spec states that `colors` should be a list of label descriptors."
            )
            warnings.warn(msg, stacklevel=1)
        else:
            dupes = duplicates(x.label_value for x in colors)
            if len(dupes) > 0:
                msg = (
                    f"Duplicated label-value: {tuple(dupes.keys())}."
                    "label-values must be unique across elements of `colors`."
                )
                raise ValueError(msg)

        return colors
