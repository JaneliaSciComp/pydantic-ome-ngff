from collections import Counter
from typing import Annotated, Any, Dict, List, Optional, Sequence, Union, cast

from pydantic import AfterValidator, BaseModel, conlist, model_validator
from pydantic_zarr.v2 import GroupSpec, ArraySpec
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.axis import Axis, AxisType
import pydantic_ome_ngff.v04.transforms as ctx

VALID_NDIM = (2, 3, 4, 5)


def ensure_scale_translation(
    transforms: Sequence[Union[ctx.VectorScale, ctx.VectorTranslation]],
) -> Sequence[Union[ctx.VectorScale, ctx.VectorTranslation]]:
    """
    Ensure that
        - the first element is a scale transformation
        - the second element is a translation transform
    """
    if len(transforms) == 0:
        raise ValueError("Invalid transforms: got 0, expected 1 or 2")

    maybe_scale = transforms[0]
    if maybe_scale.type != "scale":
        msg = (
            "The first element of coordinateTransformations must be a scale "
            f"transform. Got {maybe_scale} instead."
        )
        raise ValueError(msg)
    if len(transforms) == 2:
        maybe_trans = transforms[1]
        if (maybe_trans.type) != "translation":
            msg = (
                "The second element of coordinateTransformations must be a "
                f"translation transform. Got {maybe_trans} instead."
            )
            raise ValueError(msg)
    else:
        msg = f"Invalid number of transforms: got {len(transforms)}, expected 1 or 2"
        raise ValueError(msg)
    return transforms


def ensure_transforms_length(
    transforms: Sequence[ctx.VectorScale | ctx.VectorTranslation],
) -> Sequence[ctx.VectorScale | ctx.VectorTranslation]:
    if (num_tx := len(transforms)) not in (1, 2):
        msg = f"Invalid number of transforms: got {num_tx}, expected 1 or 2"
        raise ValueError(msg)
    return transforms


class MultiscaleDataset(StrictBase):
    """
    A single entry in the multiscales.datasets list.
    See https://ngff.openmicroscopy.org/0.4/#multiscale-md

    Attributes:
    ----------
    path: str
        The path to the zarr array that stores the image described by this metadata.
        This path should be relative to the group that contains this metadata.
    coordinateTransformations: Union[ctx.ScaleTransform, ctx.TranslationTransform]
        The coordinate transformations for this image.
    """

    path: str
    coordinateTransformations: Annotated[
        List[ctx.Scale | ctx.Translation],
        AfterValidator(ensure_transforms_length),
        AfterValidator(ensure_scale_translation),
        AfterValidator(ctx.ensure_dimensionality),
    ]


def ensure_axis_length(axes: Sequence[Axis]) -> Sequence[Axis]:
    """
    Ensure that there are between 2 and 5 axes (inclusive)
    """
    if (len_axes := len(axes)) not in VALID_NDIM:
        msg = f"Incorrect number of axes provided ({len_axes}). Only 2, 3, 4, or 5 axes are allowed."
        raise ValueError(msg)
    return axes


def ensure_axis_names(axes: Sequence[Axis]) -> Sequence[Axis]:
    """
    Ensure that the names of the axes are unique
    """
    name_dupes = duplicates(a.name for a in axes)
    if len(name_dupes) > 0:
        msg = f"Axis names must be unique. Axis names {tuple(name_dupes.keys())} are repeated."
        raise ValueError(msg)
    return axes


def ensure_axis_types(axes: Sequence[Axis]) -> Sequence[Axis]:
    """
    Ensure that the following conditions hold:
        - there are only 2 or 3 axes with type "space"
        - the axes with type "space" are last in the list of axes
        - there is only 1 axis with type "time"
        - there is only 1 axis with type "channel"
        - there is only 1 axis with a custom type
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


class Multiscale(StrictVersionedBase):
    """
    Multiscale image metadata.
    See https://ngff.openmicroscopy.org/0.4/#multiscale-md
    """

    # we need to put the version here as a private class attribute because the version
    # is not required by the spec...
    _version = version
    version: Any = version
    name: Any = None
    type: Any = None
    metadata: Optional[Dict[str, Any]] = None
    datasets: List[MultiscaleDataset]
    axes: Annotated[
        List[Axis],
        AfterValidator(ensure_axis_length),
        AfterValidator(ensure_axis_names),
        AfterValidator(ensure_axis_types),
    ]

    coordinateTransformations: List[ctx.Scale | ctx.Translation] | None = None


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
        array_items: dict[str, dict[str, ArraySpec]] = {
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
                        Union[ctx.VectorScale, ctx.VectorTranslation],
                        tform,
                    )
                    if (tform_dims := ctx.ndim(tform)) not in set(ndims):
                        msg = (
                            f"Transform {tform} has dimensionality {tform_dims} "
                            "which does notmatch the dimensionality of the arrays "
                            f"in this group ({ndims}). Transform dimensionality "
                            "must match array dimensionality."
                        )
                        raise ValueError(msg)
        return self
