from collections import Counter
from typing import Annotated, Any, Dict, List, Sequence, Union, cast

from pydantic import AfterValidator, BaseModel, Field, model_validator
from pydantic_zarr.v2 import GroupSpec, ArraySpec
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.axis import Axis, AxisType
import pydantic_ome_ngff.v04.transforms as tx
import numpy.typing as npt

VALID_NDIM = (2, 3, 4, 5)

def ensure_scale_translation(
    transforms: Sequence[Union[tx.VectorScale, tx.VectorTranslation]],
) -> Sequence[Union[tx.VectorScale, tx.VectorTranslation]]:
    """
    Ensures that the first element is a scale transformation, the second element, 
    if present, is a translation transform, and that there are only 1 or 2 transforms.
    """

    if len(transforms) == 0 or len(transforms) > 2:
        msg = f"Invalid number of transforms: got {len(transforms)}, expected 1 or 2"
        raise ValueError(msg)

    maybe_scale = transforms[0]
    if maybe_scale.type != "scale":
        msg = (
            "The first element of `coordinateTransformations` must be a scale "
            f"transform. Got {maybe_scale} instead."
        )
        raise ValueError(msg)
    if len(transforms) == 2:
        maybe_trans = transforms[1]
        if (maybe_trans.type) != "translation":
            msg = (
                "The second element of `coordinateTransformations` must be a "
                f"translation transform. Got {maybe_trans} instead."
            )
            raise ValueError(msg)

    return transforms


def ensure_transforms_length(
    transforms: Sequence[tx.VectorScale | tx.VectorTranslation],
) -> Sequence[tx.VectorScale | tx.VectorTranslation]:
    if (num_tx := len(transforms)) not in (1, 2):
        msg = f"Invalid number of transforms: got {num_tx}, expected 1 or 2"
        raise ValueError(msg)
    return transforms


class Dataset(StrictBase):
    """
    A single entry in the `multiscales.datasets` list.
    
    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.

    Attributes
    ----------
    path: str
        The path to the Zarr array that stores the image described by this metadata. This path should be relative to the group that contains this metadata.
    coordinateTransformations: ctx.ScaleTransform | ctx.TranslationTransform
        The coordinate transformations for this image.

    """

    path: str
    coordinateTransformations: Annotated[
        List[tx.Scale | tx.Translation],
        AfterValidator(ensure_transforms_length),
        AfterValidator(ensure_scale_translation),
        AfterValidator(tx.ensure_dimensionality),
    ]


def ensure_axis_length(axes: Sequence[Axis]) -> Sequence[Axis]:
    """
    Ensures that there are between 2 and 5 axes (inclusive)
    """
    if (len_axes := len(axes)) not in VALID_NDIM:
        msg = f"Incorrect number of axes provided ({len_axes}). Only 2, 3, 4, or 5 axes are allowed."
        raise ValueError(msg)
    return axes


def ensure_axis_names(axes: Sequence[Axis]) -> Sequence[Axis]:
    """
    Ensures that the names of the axes are unique.
    """
    name_dupes = duplicates(a.name for a in axes)
    if len(name_dupes) > 0:
        msg = f"Axis names must be unique. Axis names {tuple(name_dupes.keys())} are repeated."
        raise ValueError(msg)
    return axes


def ensure_axis_types(axes: Sequence[Axis]) -> Sequence[Axis]:
    """
        Ensures that the following conditions are true:

        - there are only 2 or 3 axes with type `space`
        - the axes with type `space` are last in the list of axes
        - there is only 1 axis with type `time`
        - there is only 1 axis with type `channel`
        - there is only 1 axis with a type that is not `space`, `time`, or `channel`
    """
    axis_types = [ax.type for ax in axes]
    type_census = Counter(axis_types)
    num_spaces = type_census["space"]
    if num_spaces < 2 or num_spaces > 3:
        msg = f"Invalid number of space axes: {num_spaces}. Only 2 or 3 space axes are allowed."
        raise ValueError(msg)

    elif not all(a == "space" for a in axis_types[-num_spaces:]):
        msg = f"Space axes must come last. Got axes with order: {axis_types}."
        raise ValueError(msg)

    if (num_times := type_census["time"]) > 1:
        msg = f"Invalid number of time axes: {num_times}. Only 1 time axis is allowed."
        raise ValueError(msg)

    if (num_channels := type_census["channel"]) > 1:
        msg = f"Invalid number of channel axes: {num_channels}. Only 1 channel axis is allowed."
        raise ValueError(msg)

    custom_axes = set(axis_types) - set(AxisType._member_names_)
    if (num_custom := len(custom_axes)) > 1:
        msg = f"Invalid number of custom axes: {num_custom}. Only 1 custom axis is allowed."
        raise ValueError(msg)
    return axes


class MultiscaleMetadata(StrictVersionedBase):
    """
    Multiscale image metadata.
    
    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.

    Attributes
    ----------

    name: Any
        The name for this multiscale image. Optional. Defaults to `None`.
    type: Any
        The type of the multiscale image. Optional. Defaults to `None`.
    metadata: Dict[str, Any] | None
        Metadata for this multiscale image. Optional. Defaults to `None`.
    datasets: List[MultiscaleDataset]
        A collection of descriptions of arrays that collectively comprise this multiscale image.
    axes: List[Axis]
        A list of `Axis` objects that define the semantics for the different axes of the multiscale image.
    coordinateTransformations: List[tx.Scale, tx.Translation]
        Coordinate transformations that express a scaling and translation shared by all elements of 
        `datasets`.
    """

    _version = version
    version: Any = version
    name: Any = None
    type: Any = None
    metadata: Dict[str, Any] | None = None
    datasets: Annotated[List[Dataset], Field(..., min_length=1)]
    axes: Annotated[
        List[Axis],
        AfterValidator(ensure_axis_length),
        AfterValidator(ensure_axis_names),
        AfterValidator(ensure_axis_types),
    ]
    coordinateTransformations: List[tx.Scale | tx.Translation] | None = None


class GroupAttrs(BaseModel):
    """
    A model of the required attributes of a Zarr group that implements OME-NGFF Multiscales metadata.
    
    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.    
    
    Attributes
    ----------
    multiscales: List[MultiscaleMetadata]
        A list of `MultiscaleMetadata`. Each element of `multiscales` specifies a multiscale image. 
    """

    multiscales: Annotated[List[MultiscaleMetadata], Field(..., min_length=1)]


class Group(GroupSpec[GroupAttrs, ArraySpec | GroupSpec]):
    """
    A model of a Zarr group that implements OME-NGFF Multiscales metadata.
    
    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.

    Attributes
    ----------

    attributes: MultiscaleAttrs
        The attributes of this Zarr group, which should contain valid `MultiscaleAttrs`.
    members Dict[Str, ArraySpec | GroupSpec]:
        The members of this Zarr group. Should be instances of `pydantic_zarr.GroupSpec` or `pydantic_zarr.ArraySpec`.

    """
    @classmethod
    def from_arrays(
        cls, 
        arrays: npt.NDArray[Any],
        paths: Sequence[str],
        transforms: Sequence[Sequence[tx.Transform]],
        axes: Sequence[Axis],
        *, 
        name: str | None = None, 
        type: str | None = None, 
        metadata: Dict[str, Any] | None = None,
        top_level_transforms: List[tx.Transform] | None = None, 
        **kwargs):
            """
            Create a `Group` from a sequence of arrays + spatial metadata.
            """
            members = {key: ArraySpec.from_array(arr, **kwargs) for key, arr in zip(paths, arrays, strict=True)}
            multimeta = MultiscaleMetadata(
                name=name, 
                type=type,
                metadata=metadata,
                axes=axes,
                datasets=[Dataset(path=path, coordinateTransformations=txs) for path, txs in zip(paths, transforms, strict=True)],
                coordinateTransformations=top_level_transforms)
            return cls(members=members, attributes=multimeta)

    @model_validator(mode="after")
    def check_arrays_exist(self) -> "Group":
        """
        Check that the arrays referenced in the `multiscales` metadata are actually contained in this group.

        Note that this is currently too strict, since it will not check for arrays in subgroups, but this is
        allowed by the spec. Adding tree-flattening here or in pydantic-zarr can fix this.
        """
        attrs = self.attributes
        array_items: dict[str, dict[str, ArraySpec]] = {
            k: v for k, v in self.members.items() if isinstance(v, ArraySpec)
        }

        for multiscale in attrs.multiscales:
            for dataset in multiscale.datasets:
                if (dpath := dataset.path) not in array_items:
                    msg = (
                        f"Dataset {dpath} was specified in multiscale metadata, but no "
                        "array with that name was found in the items of that group. "
                        "All arrays referenced in multiscale metadata must be items of the group."
                    )
                    raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_array_ndim(self) -> "Group":
        """
        Check that all the arrays referenced by the `multiscales` metadata have the same
        dimensionality, and that this dimensionality is consistent with the `coordinateTransformations` metadata.
        """
        attrs = self.attributes
        array_items: dict[str, ArraySpec] = {
            k: v for k, v in self.members.items() if isinstance(v, ArraySpec)
        }

        ndims = tuple(len(a.shape) for a in array_items.values())
        if len(set(ndims)) > 1:
            msg = (
                "All arrays must have the same dimensionality. "
                f"Got arrays with dimensionality {ndims}."
            )
            raise ValueError(msg)

        # check that each transform has compatible rank
        for multiscale in attrs.multiscales:
            tforms = []
            if multiscale.coordinateTransformations is not None:
                tforms.extend(multiscale.coordinateTransformations)
            for dataset in multiscale.datasets:
                tforms.extend(dataset.coordinateTransformations)
            for tform in tforms:
                if hasattr(tform, "scale") or hasattr(tform, "translation"):
                    tform = cast(
                        Union[tx.VectorScale, tx.VectorTranslation],
                        tform,
                    )
                    if (tform_dims := tx.ndim(tform)) not in set(ndims):
                        msg = (
                            f"Transform {tform} has dimensionality {tform_dims} "
                            "which does not match the dimensionality of the arrays "
                            f"in this group ({ndims}). Transform dimensionality "
                            "must match array dimensionality."
                        )
                        raise ValueError(msg)
        return self
