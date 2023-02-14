import warnings
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, ValidationError, validator

from pydantic_ome_ngff.base import StrictBaseModel, warning_on_one_line
from pydantic_ome_ngff.v05 import version
from pydantic_ome_ngff.v05.axes import Axis, AxisType
from pydantic_ome_ngff.v05.coordinateTransformations import (
    ScaleTransform,
    TranslationTransform,
)

warnings.formatwarning = warning_on_one_line


class MultiscaleDataset(StrictBaseModel):
    path: str
    coordinateTransformations: Union[
        List[ScaleTransform], List[Union[ScaleTransform, TranslationTransform]]
    ]


class Multiscale(StrictBaseModel):
    # SPEC: why is this optional?
    # SPEC: untyped!
    version: Optional[Any] = version
    # SPEC: why is this nullable instead of reserving the empty string
    # SPEC: untyped!
    name: Optional[Any]
    # SPEC: not clear what this field is for, given the existence of .metadata
    # SPEC: untyped!
    type: Optional[Any]
    # SPEC: should default to empty dict instead of None
    metadata: Optional[Dict[str, Any]] = None
    datasets: List[MultiscaleDataset]
    # SPEC: should not exist at top level and instead
    # live in dataset metadata or in .datasets
    axes: List[Axis] = Field(..., min_items=2, max_items=5)
    # SPEC: should not live here, and if it is here,
    # it should default to an empty list instead of being nullable
    coordinateTransformations: Optional[
        List[Union[ScaleTransform, TranslationTransform]]
    ]

    @validator("name")
    def normative_name(cls, name):
        if name is None:
            warnings.warn(
                f"""
            The name field was set to None.
            Version {version} of the OME-NGFF spec states that
            the `name` field of a Multiscales object should not be None.
            """
            )
        return name

    @validator("axes")
    def normative_axes(cls, axes):
        axis_types = [a.type for a in axes]
        type_census = {
            name: sum(map(lambda v: v == name, axis_types))
            for name in AxisType._member_names_
        }

        num_spaces = type_census["space"]
        if num_spaces < 2 or num_spaces > 3:
            raise ValidationError(
                f"""
                Invalid number of space axes ({num_spaces}).
                Only 2 or 3 space axes are allowed.
                """
            )

        elif not all(a == "space" for a in axis_types[-num_spaces:]):
            raise ValidationError(
                f"""
                Space axes must come last.
                Got axis ordered {axis_types}
                """
            )

        num_times = type_census["time"]

        if num_times > 1:
            raise ValidationError(
                f"""
                Invalid number of time axes ({num_times}).
                Only 1 time axis is allowed."""
            )

        num_channels = type_census["channel"]

        if num_channels > 1:
            raise ValidationError(
                f"""
                Invalid number of time axes ({num_times}).
                Only 1 time axis is allowed.
                """
            )

        custom_axes = set(axis_types) - set(AxisType._member_names_)
        if len(custom_axes) > 1:
            raise ValidationError(
                f"""Invalid number of custom axes ({custom_axes}).
                Only 1 custom axis is allowed.
                """
            )
        return axes
