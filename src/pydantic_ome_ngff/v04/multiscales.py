from __future__ import annotations
from collections import Counter
import textwrap
import warnings
from typing import Any, Dict, List, Optional, Union, cast

from pydantic import BaseModel, conlist, model_validator, field_validator
from pydantic_zarr.v2 import GroupSpec, ArraySpec
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.axes import Axis, AxisType
import pydantic_ome_ngff.v04.coordinateTransformations as ctx


class MultiscaleDataset(BaseModel):
    path: str
    coordinateTransformations: conlist(
        Union[ctx.ScaleTransform, ctx.TranslationTransform], min_length=1, max_length=2
    )

    @field_validator("coordinateTransformations")
    def check_transforms_dimensionality(
        cls,
        transforms: List[
            Union[ctx.VectorScaleTransform, ctx.VectorTranslationTransform]
        ],
    ) -> List[Union[ctx.VectorScaleTransform, ctx.VectorTranslationTransform]]:
        ndims = []
        for tx in transforms:
            # this repeated conditional logic around transforms is so awful.
            if type(tx) in (ctx.VectorScaleTransform, ctx.VectorTranslationTransform):
                ndims.append(ctx.get_transform_ndim(tx))
        if len(set(ndims)) > 1:
            msg = (
                "Elements of coordinateTransformations must have the same "
                f"dimensionality. Got elements with dimensionality = {ndims}."
            )
            raise ValueError(msg)
        return transforms

    @field_validator("coordinateTransformations")
    def check_transforms_types(
        cls,
        transforms: List[
            Union[ctx.VectorScaleTransform, ctx.VectorTranslationTransform]
        ],
    ) -> List[Union[ctx.VectorScaleTransform, ctx.VectorTranslationTransform]]:
        if (tform := transforms[0].type) != "scale":
            msg = (
                "The first element of coordinateTransformations must be a scale "
                f"transform. Got {tform} instead."
            )
            raise ValueError(msg)
        if len(transforms) == 2:
            if (tform := transforms[1].type) != "translation":
                msg = (
                    "The second element of coordinateTransformations must be a "
                    f"translation transform. got {tform} instead."
                )
                raise ValueError(msg)
        return transforms


class Multiscale(VersionedBase):
    """
    Multiscale image metadata.
    See https://ngff.openmicroscopy.org/0.4/#multiscale-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    # SPEC: why is this optional? why is it untyped?
    version: Optional[Any] = version
    # SPEC: why is this nullable instead of reserving the empty string
    # SPEC: untyped!
    name: Optional[Any] = None
    # SPEC: not clear what this field is for, given the existence of .metadata
    # SPEC: untyped!
    type: Any = None
    # SPEC: should default to empty dict instead of None
    metadata: Optional[Dict[str, Any]] = None
    datasets: List[MultiscaleDataset]
    # SPEC: should not exist at top level and instead
    # live in dataset metadata or in .datasets
    axes: conlist(Axis, min_length=2, max_length=5)
    # SPEC: should not live here, and if it is here,
    # it should default to an empty list instead of being nullable
    coordinateTransformations: Optional[
        List[Union[ctx.ScaleTransform, ctx.TranslationTransform]]
    ] = None

    @field_validator("name")
    def check_name(cls, name: str) -> str:
        if name is None:
            msg = (
                f"The name field was set to None. Version {cls._version} "
                "of the OME-NGFF spec states that the `name` field of a Multiscales "
                "object should not be None."
            )
            warnings.warn(msg)
        return name

    @field_validator("axes")
    def check_axes(cls, axes: List[Axis]) -> List[Axis]:
        name_dupes = duplicates(a.name for a in axes)
        if len(name_dupes) > 0:
            msg = (
                f"Axis names must be unique. Axis names {tuple(name_dupes.keys())} "
                "are repeated."
            )
            raise ValueError(textwrap.fill(msg))
        axis_types = [ax.type for ax in axes]
        type_census = Counter(axis_types)
        num_spaces = type_census["space"]
        if num_spaces < 2 or num_spaces > 3:
            msg = (
                f"Invalid number of space axes: {num_spaces}. Only 2 or 3 space "
                "axes are allowed."
            )
            raise ValueError(textwrap.fill(msg))

        elif not all(a == "space" for a in axis_types[-num_spaces:]):
            msg = f"Space axes must come last. Got axes with order: {axis_types}"
            raise ValueError(textwrap.fill(msg))

        if (num_times := type_census["time"]) > 1:
            msg = (
                f"Invalid number of time axes: {num_times}. "
                "Only 1 time axis is allowed."
            )
            raise ValueError(textwrap.fill(msg))

        if (num_channels := type_census["channel"]) > 1:
            msg = (
                f"Invalid number of channel axes: {num_channels}. "
                "Only 1 channel axis is allowed."
            )
            raise ValueError(textwrap.fill(msg))

        custom_axes = set(axis_types) - set(AxisType._member_names_)
        if len(custom_axes) > 1:
            msg = (
                f"Invalid number of custom axes: {custom_axes}. "
                "Only 1 custom axis is allowed."
            )
            raise ValueError(textwrap.fill(msg))
        return axes


class MultiscaleAttrs(BaseModel):
    """
    Attributes of a multiscale group.
    See https://ngff.openmicroscopy.org/0.4/#multiscale-md
    """

    multiscales: conlist(Multiscale, min_length=1)


class MultiscaleGroup(GroupSpec[MultiscaleAttrs, Union[ArraySpec, GroupSpec]]):
    @model_validator(mode="after")
    def check_arrays_exist(self) -> "MultiscaleGroup":

        attrs = self.attributes
        array_items: dict[str, dict[str, Any]] = {
            k: v for k, v in self.members.items() if isinstance(v, ArraySpec)
        }
        multiscales: List[Multiscale] = attrs.multiscales

        for multiscale in multiscales:
            for dataset in multiscale.datasets:
                if (dpath := dataset.path) not in array_items:
                    msg = (
                        f"Dataset {dpath} was specified in multiscale metadata, but no "
                        "array with that name was found in the items of that group. "
                        "All arrays in multiscale metadata must be items of the group."
                    )
                    raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_array_ndim(self) -> "MultiscaleGroup":
        attrs = self.attributes
        array_items: dict[str, ArraySpec] = {
            k: v for k, v in self.members.items() if isinstance(v, ArraySpec)
        }
        multiscales: List[Multiscale] = attrs.multiscales

        ndims = tuple(len(a.shape) for a in array_items.values())
        if len(set(ndims)) > 1:
            msg = (
                "All arrays must have the same dimensionality. "
                f"Got arrays with dimensionality {ndims}."
            )
            raise ValueError(msg)

        # check that each transform has compatible rank
        for multiscale in multiscales:
            tforms = []
            if multiscale.coordinateTransformations is not None:
                tforms.extend(multiscale.coordinateTransformations)
            for dataset in multiscale.datasets:
                tforms.extend(dataset.coordinateTransformations)
            for tform in tforms:
                if hasattr(tform, "scale") or hasattr(tform, "translation"):
                    tform = cast(
                        Union[ctx.VectorScaleTransform, ctx.VectorTranslationTransform],
                        tform,
                    )
                    if (tform_dims := ctx.get_transform_ndim(tform)) not in set(ndims):
                        msg = (
                            f"Transform {tform} has dimensionality {tform_dims} "
                            "which does notmatch the dimensionality of the arrays "
                            f"in this group ({ndims}). Transform dimensionality "
                            "must match array dimensionality."
                        )
                        raise ValueError(msg)
        return self
