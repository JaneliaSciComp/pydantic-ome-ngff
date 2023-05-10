from __future__ import annotations
from collections import Counter
from typing import Any, Dict, List, Tuple, cast
import warnings

from pydantic import conlist, root_validator, validator
from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.latest.base import version
from pydantic_ome_ngff.latest import coordinateTransformations as ctx
from pydantic_ome_ngff.tree import Array, Attrs, Group
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.v04.axes import AxisType
from pydantic_ome_ngff.latest.axes import Axis


class MultiscaleDataset(StrictBase):
    path: str
    coordinateTransformations: conlist(
        ctx.ScaleTransform | ctx.TranslationTransform, min_items=1, max_items=2
    )

    @validator("coordinateTransformations")
    def check_transforms_dimensionality(
        cls,
        transforms: List[ctx.VectorScaleTransform | ctx.VectorTranslationTransform],
    ) -> List[ctx.VectorScaleTransform | ctx.VectorTranslationTransform]:
        ndims = []
        for tx in transforms:
            # this repeated conditional logic around transforms is so awful.
            if type(tx) in (ctx.VectorScaleTransform, ctx.VectorTranslationTransform):
                ndims.append(ctx.get_transform_ndim(tx))
        if len(set(ndims)) > 1:
            msg = f"""
            Elements of coordinateTransformations must have the same dimensionality. Got
            elements with dimensionality = {ndims}.
            """
            raise ValueError(msg)
        return transforms

    @validator("coordinateTransformations")
    def check_transforms_types(
        cls, transforms: List[ctx.CoordinateTransform]
    ) -> List[ctx.CoordinateTransform]:
        if (tform := transforms[0].type) != "scale":
            msg = f"""
            The first element of coordinateTransformations must be a scale transform.
            Got {tform} instead.
            """
            raise ValueError(msg)
        if len(transforms) == 2:
            if (tform := transforms[1].type) != "translation":
                msg = f"""
                The second element of coordinateTransformations must be a translation 
                transform. got {tform} instead.
                """
                raise ValueError(msg)
        return transforms


class Multiscale(StrictVersionedBase):
    """
    Multiscale image metadata.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    # SPEC: why is this optional? why is it untyped?
    version: Any | None = version
    # SPEC: why is this nullable instead of reserving the empty string
    # SPEC: untyped!
    name: Any | None
    # SPEC: not clear what this field is for, given the existence of .metadata
    # SPEC: untyped!
    type: Any | None
    # SPEC: should default to empty dict instead of None
    metadata: Dict[str, Any] | None = None
    datasets: List[MultiscaleDataset]
    # SPEC: should not exist at top level and instead
    # live in dataset metadata or in .datasets
    axes: conlist(Axis, min_items=2, max_items=5)
    # SPEC: should not live here, and if it is here,
    # it should default to an empty list instead of being nullable
    coordinateTransformations: List[
        ctx.ScaleTransform | ctx.TranslationTransform
    ] | None

    @validator("name")
    def check_name(cls, name: str | None) -> str | None:
        if name is None:
            msg = f"""
            The name field was set to None. Version {cls._version} of the OME-NGFF spec 
            states that the `name` field of a Multiscales object should not be None.
            """
            warnings.warn(msg)
        return name

    @validator("axes")
    def check_axes(cls, axes: List[Axis]) -> List[Axis]:
        name_dupes = duplicates(a.name for a in axes)
        if len(name_dupes) > 0:
            msg = f"""
                Axis names must be unique. Axis names {tuple(name_dupes.keys())} are 
                repeated.
                """
            raise ValueError(msg)
        axis_types = tuple(ax.type for ax in axes)
        type_census = Counter(axis_types)
        num_spaces = type_census["space"]
        if num_spaces < 2 or num_spaces > 3:
            msg = f"""
                Invalid number of space axes: {num_spaces}. Only 2 or 3 space axes 
                are allowed.
                """
            raise ValueError(msg)

        elif not all(a == "space" for a in axis_types[-num_spaces:]):
            msg = f"""
                Space axes must come last. Got axes with order: {axis_types}
                """
            raise ValueError(msg)

        if (num_times := type_census["time"]) > 1:
            msg = f"""
                Invalid number of time axes: {num_times}. Only 1 time axis is allowed.
                """
            raise ValueError(msg)

        if (num_channels := type_census["channel"]) > 1:
            msg = f"""
                Invalid number of channel axes: {num_channels}. Only 1 channel axis is 
                allowed.
                """
            raise ValueError(msg)

        custom_axes = set(axis_types) - set(AxisType._member_names_)
        if len(custom_axes) > 1:
            msg = f"""Invalid number of custom axes: {custom_axes}. 
            Only 1 custom axis is allowed.
            """
            raise ValueError(msg)
        return axes


class MultiscaleAttrs(Attrs):
    """
    Attributes of a multiscale group.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md
    """

    multiscales: List[Multiscale]


class MultiscaleGroup(Group):
    attrs: MultiscaleAttrs

    @root_validator
    def check_arrays_exist(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        children: List[Array | Group] = values["children"]
        child_arrays = []
        child_groups = []

        for child in children:
            if isinstance(child, Group):
                child_groups.append(child)
            else:
                child_arrays.append(child)
        child_array_names = [a.name for a in child_arrays]
        multiscales: List[Multiscale] = values["attrs"].multiscales
        for multiscale in multiscales:
            for dataset in multiscale.datasets:
                if (dpath := dataset.path) not in child_array_names:
                    msg = f"""
                    Dataset {dpath} was specified in multiscale metadata, but no 
                    array with that name was found in the children of that group. All 
                    arrays in multiscale metadata must be children of the group.
                    """
                    raise ValueError(msg)
        return values

    @root_validator
    def check_array_ndim(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        array_children: Tuple[Array, ...] = tuple(
            filter(lambda v: hasattr(v, "shape"), values["children"])
        )
        multiscales: List[Multiscale] = values["attrs"].multiscales

        ndims = [len(a.shape) for a in array_children]
        if len(set(ndims)) > 1:
            msg = f"""
            All arrays must have the same dimensionality. Got arrays with dimensionality
            {ndims}. 
            """
            raise ValueError(msg)

        # check that each transform has compatible rank
        for multiscale in multiscales:
            tforms: List[ctx.CoordinateTransform] = []
            if multiscale.coordinateTransformations is not None:
                tforms.extend(multiscale.coordinateTransformations)
            for dataset in multiscale.datasets:
                tforms.extend(dataset.coordinateTransformations)
            for tform in tforms:
                if hasattr(tform, "scale") or hasattr(tform, "translation"):
                    tform = cast(
                        ctx.VectorScaleTransform | ctx.VectorTranslationTransform,
                        tform,
                    )
                    if (tform_dims := ctx.get_transform_ndim(tform)) not in set(ndims):
                        msg = f"""
                        Transform {tform} has dimensionality {tform_dims} which does not
                        match the dimensionality of the arrays in this group ({ndims}). 
                        Transform dimensionality must match array 
                        dimensionality.
                        """
                        raise ValueError(msg)
        return values
