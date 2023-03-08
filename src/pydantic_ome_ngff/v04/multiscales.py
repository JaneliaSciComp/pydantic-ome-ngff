from collections import Counter
import warnings
from typing import Any, Dict, List, Optional, Union, Tuple, cast

from pydantic import Field, root_validator, validator

from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.tree import Group, Attrs, Array
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.axes import Axis, AxisType
from pydantic_ome_ngff.v04.coordinateTransformations import (
    ScaleTransform,
    TranslationTransform,
    VectorScaleTransform,
    VectorTranslationTransform,
    get_transform_rank,
)


class MultiscaleDataset(StrictBase):
    path: str
    coordinateTransformations: List[
        Union[ScaleTransform, TranslationTransform]
    ] = Field(..., min_items=1, max_items=2)

    @validator("coordinateTransformations")
    def check_transforms_rank(cls, transforms):
        ranks = []
        for tx in transforms:
            # this repeated conditional logic around transforms is so awful.
            if type(tx) in (VectorScaleTransform, VectorTranslationTransform):
                ranks.append(get_transform_rank(tx))
        if len(set(ranks)) > 1:
            raise ValueError(
                f"""
            Elements of coordinateTransformations must have the same dimensionality. Got
            elements with dimensionality = {ranks}.
            """
            )
        return transforms

    @validator("coordinateTransformations")
    def check_transforms_types(cls, transforms):
        if (tform := transforms[0].type) != "scale":
            raise ValueError(
                f"""
            The first element of coordinateTransformations must be a scale transform.
            Got {tform} instead.
            """
            )

        if (tform := transforms[1].type) != "translation":
            raise ValueError(
                f"""
            The second element of coordinateTransformations must be a translation 
            transform. got {tform} instead.
            """
            )
        return transforms


class Multiscale(StrictVersionedBase):
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
    def check_name(cls, name):
        if name is None:
            warnings.warn(
                f"""
            The name field was set to None. Version {cls._version} of the OME-NGFF spec 
            states that the `name` field of a Multiscales object should not be None.
            """
            )
        return name

    @validator("axes")
    def check_axes(cls, axes):
        name_dupes = duplicates(a.name for a in axes)
        if len(name_dupes) > 0:
            raise ValueError(
                f"""
                Axis names must be unique. Axis names {tuple(name_dupes.keys())} are 
                repeated.
                """
            )
        axis_types = [ax.type for ax in axes]
        type_census = Counter(axis_types)
        num_spaces = type_census["space"]
        if num_spaces < 2 or num_spaces > 3:
            raise ValueError(
                f"""
                Invalid number of space axes: {num_spaces}. Only 2 or 3 "space" axes 
                are allowed.
                """
            )

        elif not all(a == "space" for a in axis_types[-num_spaces:]):
            raise ValueError(
                f"""
                Space axes must come last. Got axes with order: {axis_types}
                """
            )

        if (num_times := type_census["time"]) > 1:
            raise ValueError(
                f"""
                Invalid number of time axes: {num_times}. Only 1 time axis is allowed.
                """
            )

        if (num_channels := type_census["channel"]) > 1:
            raise ValueError(
                f"""
                Invalid number of channel axes: {num_channels}. Only 1 channel axis is 
                allowed.
                """
            )

        custom_axes = set(axis_types) - set(AxisType._member_names_)
        if len(custom_axes) > 1:
            raise ValueError(
                f"""Invalid number of custom axes: {custom_axes}. Only 1 custom axis is
                allowed.
                """
            )
        return axes


class MultiscaleAttrs(Attrs):
    """
    Attributes of a multiscale group.
    See https://ngff.openmicroscopy.org/0.4/#multiscale-md
    """

    multiscales: List[Multiscale]


class MultiscaleGroup(Group):
    attrs: MultiscaleAttrs

    @root_validator
    def check_arrays_exist(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        children: List[Union[Array, Group]] = values["children"]
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
                    raise ValueError(
                        f"""
                    Dataset {dpath} was specified in multiscale metadata, but no 
                    array with that name was found in the children of that group. All 
                    arrays in multiscale metadata must be children of the group.
                    """
                    )
        return values

    @root_validator
    def check_ranks(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        array_children: Tuple[Array, ...] = tuple(
            filter(lambda v: hasattr(v, "shape"), values["children"])
        )
        multiscales: List[Multiscale] = values["attrs"].multiscales

        ranks = [len(a.shape) for a in array_children]
        if len(set(ranks)) > 1:
            raise ValueError(
                f"""
            All arrays must have the same dimensionality. Got arrays with dimensionality
            {ranks}. 
            """
            )

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
                        Union[VectorScaleTransform, VectorTranslationTransform], tform
                    )
                    if (tform_dims := get_transform_rank(tform)) not in set(ranks):
                        raise ValueError(
                            f"""
                        Transform {tform} has dimensionality {tform_dims} which does not
                        match the dimensionality of the arrays in this group ({ranks}). 
                        Transform dimensionality must match array 
                        dimensionality.
                        """
                        )
        return values
