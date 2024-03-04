from __future__ import annotations
import warnings
from typing import List, Literal, Optional, Tuple, Annotated

from pydantic import AfterValidator, BaseModel, Field, model_validator
from pydantic_ome_ngff.base import VersionedBase
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.v04.base import version as NGFF_VERSION

import pydantic_ome_ngff.v04.multiscales as multiscales

ConInt = Annotated[int, Field(strict=True, ge=0, le=255)]
RGBA = Tuple[ConInt, ConInt, ConInt, ConInt]


class Color(BaseModel):
    """
    A label value and RGBA as defined in https://ngff.openmicroscopy.org/0.4/#label-md
    """

    label_value: int = Field(..., serialization_alias="label-value")
    rgba: Optional[RGBA]


class Source(BaseModel):
    # todo: add validation that this path resolves to something
    image: Optional[str] = "../../"


class Property(BaseModel):
    label_value: int = Field(..., serialization_alias="label-value")


def parse_colors(colors: List[Color] | None) -> List[Color] | None:
    if colors is None:
        msg = (
            f"The field `colors` is `None`. Version {NGFF_VERSION} of"
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


def parse_version(version: Literal["0.4"] | None) -> Literal["0.4"] | None:
    if version is None:
        _ = (
            f"The `version` attribute is `None`. Version {NGFF_VERSION} of "
            f"the OME-NGFF spec states that `version` should either be unset or the string {NGFF_VERSION}"
        )
        # This goes against a recommendation from the spec, but emitting a warning is annoying.
        # leaving this here as a placeholder.
    return version


def parse_imagelabel(model: ImageLabel):
    """
    check that label_values are consistent across properties and colors
    """
    if model.colors is not None and model.properties is not None:
        prop_label_value = [prop.label_value for prop in model.properties]
        color_label_value = [color.label_value for color in model.colors]

        prop_label_value_set = set(prop_label_value)
        color_label_value_set = set(color_label_value)
        if color_label_value_set != prop_label_value_set:
            msg = (
                "Inconsistent `label_value` attributes in `colors` and `properties`."
                f"The `properties` attributes have `label_values` {prop_label_value}, "
                f"The `colors` attributes have `label_values` {color_label_value}, "
            )
            raise ValueError(msg)
    return model


class ImageLabel(VersionedBase):
    """
    image-label metadata.
    See https://ngff.openmicroscopy.org/0.4/#label-md
    """

    _version: Literal["0.4"] = NGFF_VERSION

    version: Annotated[
        Literal["0.4"] | None, AfterValidator(parse_version)
    ] = NGFF_VERSION
    colors: Annotated[Optional[List[Color]], AfterValidator(parse_colors)] = None
    properties: Optional[List[Property]] = None
    source: Optional[Source] = None

    @model_validator(mode="after")
    def parse_model(self):
        return parse_imagelabel(self)


class GroupAttrs(multiscales.GroupAttrs):
    """
    Attributes for a Zarr group that contains `image-label` metadata.
    Inherits from `v04.multiscales.MultiscaleAttrs`.

    See https://ngff.openmicroscopy.org/0.4/#label-md

    Attributes
    ----------
    image_label: `ImageLabel`
        Image label metadata.
    multiscales: List[v04.multiscales.Multiscales]
        Multiscale image metadata.
    """

    image_label: Annotated[ImageLabel, Field(..., serialization_alias="image-label")]


class Group(multiscales.Group):
    attributes: GroupAttrs
