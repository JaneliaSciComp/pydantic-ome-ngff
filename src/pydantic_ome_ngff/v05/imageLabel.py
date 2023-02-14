import warnings
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError, validator

from pydantic_ome_ngff.v05 import version as v05_version


class Color(BaseModel):
    label_value: int = Field(..., alias="label-value")
    rgba: Optional[Tuple[int, int, int, int]]


class Source(BaseModel):
    image: Optional[str] = "../../"


class Properties(BaseModel):
    label_value: int = Field(..., alias="label-value")


class ImageLabel(BaseModel):
    version: Optional[str] = v05_version
    colors: Optional[List[Color]]
    properties: Optional[Properties]
    source: Optional[Source]

    @validator("version")
    def normative_version(cls, version):
        if version is None:
            warnings.warn(
                f"""
            The field `version` is null. Version {v05_version} of
            the OME-NGFF spec states that the `version` field should be {v05_version}.
            """
            )
        return version

    @validator("colors")
    def normative_colors(cls, colors):
        if colors is None:
            warnings.warn(
                f"""
            The field `colors` is null. Version {v05_version} of
            the OME-NGFF spec states that the `colors` field
            should be a list of label descriptors.
            """
            )
        else:
            values = [x.label_value for x in colors]
            if len(set(values)) < len(colors):
                dupes = []
                for v in set(values):
                    if values.count(v) > 1:
                        dupes.append(v)

                raise ValidationError(
                    f"""
                    Duplicated label-value: {dupes}.
                    label-values must be unique across elements of `colors`
                    """
                )

        return colors
