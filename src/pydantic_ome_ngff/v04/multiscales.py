import warnings
from typing import Any, Dict, List, Optional, Union, Tuple, cast

from pydantic import root_validator, validator

from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.tree import Group, Attrs, Array
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.axes import Axes
import pydantic_ome_ngff.v04.coordinateTransformations as ctx


class MultiscaleDataset(StrictBase):
    path: str
    coordinateTransformations: ctx.Transforms


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
    axes: Axes
    # SPEC: should not live here, and if it is here,
    # it should default to an empty list instead of being nullable
    coordinateTransformations: Optional[ctx.Transforms]

    @validator("datasets")
    def check_datasets_tform_ndim(cls, v):
        ndims = [ds.coordinateTransformations.ndim for ds in v]
        if len(set(ndims)) > 1:
            raise ValueError
        return v

    @validator("name")
    def check_name(cls, name: str) -> str:
        if name is None:
            msg = (
                f"The name field was set to None. Version {cls._version} of the "
                "OME-NGFF spec states that the `name` field of a Multiscales object "
                "should not be None."
            )
            warnings.warn(msg)
        return name

    @root_validator
    def check_axes_transforms(cls, v: Any):
        if "datasets" in v and "axes" in v:
            ds_ndims = v["datasets"][0].coordinateTransformations.ndim
            if len(v["axes"]) != ds_ndims:
                msg = (
                    f"Mismatched dimensionality. Number of axes ({len(v['axes'])}) "
                    "does not align with the dimensionality of the coordinate "
                    f"transformations defined in the datasets ({ds_ndims})."
                )
                raise ValueError(msg)
        return v


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
    def check_array_ndim(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        array_children: Tuple[Array, ...] = tuple(
            filter(lambda v: hasattr(v, "shape"), values["children"])
        )
        multiscales: List[Multiscale] = values["attrs"].multiscales

        ndims = tuple(len(a.shape) for a in array_children)
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
                    if (tform_dims := tform.ndim) not in set(ndims):
                        raise ValueError(
                            f"""
                        Transform {tform} has dimensionality {tform_dims} which does not
                        match the dimensionality of the arrays in this group ({ndims}). 
                        Transform dimensionality must match array 
                        dimensionality.
                        """
                        )
        return values
