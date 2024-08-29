from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

import numpy as np
from typing_extensions import Literal, deprecated

if TYPE_CHECKING:
    from numcodecs.abc import Codec
    from typing_extensions import Self

from typing import Annotated, Any, Sequence, cast

import zarr
from numcodecs import Zstd
from pydantic import AfterValidator, BaseModel, Field, model_validator
from pydantic_zarr.v2 import ArraySpec, GroupSpec
from zarr.errors import ArrayNotFoundError, ContainsGroupError
from zarr.util import guess_chunks

import pydantic_ome_ngff.v04.transform as tx
from pydantic_ome_ngff.base import FrozenBase, NoneSkipBase, VersionedBase
from pydantic_ome_ngff.utils import (
    ArrayLike,
    ChunkedArrayLike,
    duplicates,
    get_path,
)
from pydantic_ome_ngff.v04.axis import Axis, AxisType
from pydantic_ome_ngff.v04.base import version

VALID_NDIM = (2, 3, 4, 5)
NUM_TX_MAX = 2
DEFAULT_COMPRESSOR = Zstd(3)


def ensure_scale_translation(
    transforms: Sequence[tx.VectorScale | tx.VectorTranslation],
) -> Sequence[tx.VectorScale | tx.VectorTranslation]:
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
    if len(transforms) == NUM_TX_MAX:
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


class Dataset(FrozenBase):
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
        tuple[tx.Scale] | tuple[tx.Scale, tx.Translation],
        AfterValidator(ensure_scale_translation),
        AfterValidator(tx.ensure_dimensionality),
    ]


# consider making this a classmethod of `Dataset`
def create_dataset(
    path: str, scale: Sequence[int | float], translation: Sequence[int | float]
) -> Dataset:
    """
    Create a `Dataset` from a path, a scale, and a translation. This metadata models a Zarr array that partially comprises a multiscale group.

    Parameters
    ----------

    path: str
        The path, relative to the multiscale group, of the Zarr array.
    scale: Sequence[int | float]:
        The scale parameter for data stored in the Zarr array. This should define the spacing between elements of the coordinate grid of the data.
    translation: Sequence[int | float]:
        The translation parameter for data stored in the Zarr array. This should define the origin of the coordinate grid of the data.

    Returns
    -------

    `Dataset`
    """
    return Dataset(
        path=path,
        coordinateTransformations=(
            tx.scale_translation(scale=scale, translation=translation)
        ),
    )


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

    if not all(a == "space" for a in axis_types[-num_spaces:]):
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


class MultiscaleMetadata(VersionedBase, FrozenBase, NoneSkipBase):
    """
    Multiscale image metadata.

    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.

    Attributes
    ----------

    name: Any, default = `None`
        The name for this multiscale image. Optional. Defaults to `None`.
    type: Any, default = `None`
        The type of the multiscale image. Optional. Defaults to `None`.
    metadata: Dict[str, Any] | None, default = `None`
        Metadata for this multiscale image. Optional. Defaults to `None`.
    datasets: tuple[Dataset, ...]
        A collection of descriptions of arrays that collectively comprise this multiscale image.
    axes: tuple[Axis, ...]
        A tuple of `Axis` objects that define the semantics for the different axes of the multiscale image.
    coordinateTransformations: tuple[tx.Scale] | tuple[tx.Scale, tx.Translation] | None. Defaults to `None`.
        Coordinate transformations that express a scaling and translation shared by all elements of
        `datasets`. Defaults to `None`.
    """

    _version = version
    _skip_if_none: tuple[
        Literal["name"],
        Literal["coordinateTransformations"],
        Literal["type"],
        Literal["metadata"],
    ] = ("name", "coordinateTransformations", "type", "metadata")
    version: Any = version
    name: Any = None
    type: Any = None
    metadata: dict[str, Any] | None = None
    datasets: Annotated[tuple[Dataset, ...], Field(..., min_length=1)]
    axes: Annotated[
        tuple[Axis, ...],
        AfterValidator(ensure_axis_length),
        AfterValidator(ensure_axis_names),
        AfterValidator(ensure_axis_types),
    ]
    coordinateTransformations: (
        tuple[tx.Scale] | tuple[tx.Scale, tx.Translation] | None
    ) = None

    @model_validator(mode="after")
    def validate_transforms(self) -> MultiscaleMetadata:
        """
        Ensure that the dimensionality of the top-level coordinateTransformations, if present,
        is consistent with the rest of the model.
        """
        ctx = self.coordinateTransformations
        if ctx is not None:
            # check that the dimensionality is internally consistent
            tx.ensure_dimensionality(ctx)

            # check that the dimensionality matches the dimensionality of the dataset ctx
            ndim = ctx[0].ndim
            dset_scale_ndim = self.datasets[0].coordinateTransformations[0].ndim
            if ndim != dset_scale_ndim:
                msg = (
                    f"Dimensionality of multiscale.coordinateTransformations {ndim} "
                    "does not match dimensionality of coordinateTransformations defined in"
                    f"multiscale.datasets ({dset_scale_ndim}) "
                )
                raise ValueError(msg)

        return self


class MultiscaleGroupAttrs(BaseModel):
    """
    A model of the required attributes of a Zarr group that implements OME-NGFF Multiscales metadata.

    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.

    Attributes
    ----------
    multiscales: tuple[MultiscaleMetadata]
        A list of `MultiscaleMetadata`. Each element of `multiscales` specifies a multiscale image.
    """

    multiscales: Annotated[tuple[MultiscaleMetadata, ...], Field(..., min_length=1)]


class MultiscaleGroup(GroupSpec[MultiscaleGroupAttrs, ArraySpec | GroupSpec]):
    """
    A model of a Zarr group that implements OME-NGFF Multiscales metadata.

    See [https://ngff.openmicroscopy.org/0.4/#multiscale-md](https://ngff.openmicroscopy.org/0.4/#multiscale-md) for the specification of this data structure.

    Attributes
    ----------

    attributes: GroupAttrs
        The attributes of this Zarr group, which should contain valid `GroupAttrs`.
    members: Dict[Str, ArraySpec | GroupSpec]:
        The members of this Zarr group. Should be instances of `pydantic_zarr.GroupSpec` or `pydantic_zarr.ArraySpec`.

    """

    @classmethod
    def from_zarr(cls, node: zarr.Group) -> MultiscaleGroup:
        """
        Create an instance of `Group` from a `node`, a `zarr.Group`. This method discovers Zarr arrays in the hierarchy rooted at `node` by inspecting the OME-NGFF
        multiscales metadata.

        Parameters
        ---------
        node: zarr.Group
            A Zarr group that has valid OME-NGFF multiscale metadata.

        Returns
        -------
        Group
            A model of the Zarr group.
        """
        # on unlistable storage backends, the members of this group will be {}
        guess = GroupSpec.from_zarr(node, depth=0)

        try:
            multi_meta_maybe = guess.attributes["multiscales"]
        except KeyError as e:
            store_path = get_path(node.store)
            msg = (
                "Failed to find mandatory `multiscales` key in the attributes of the Zarr group at "
                f"{node.store}://{store_path}://{node.path}."
            )
            raise KeyError(msg) from e

        multi_meta = MultiscaleGroupAttrs(multiscales=multi_meta_maybe)
        members_tree_flat = {}
        for multiscale in multi_meta.multiscales:
            for dataset in multiscale.datasets:
                array_path = f"{node.path}/{dataset.path}"
                try:
                    array = zarr.open_array(store=node.store, path=array_path, mode="r")
                    array_spec = ArraySpec.from_zarr(array)
                except ArrayNotFoundError as e:
                    msg = (
                        f"Expected to find an array at {array_path}, "
                        "but no array was found there."
                    )
                    raise ValueError(msg) from e
                except ContainsGroupError as e:
                    msg = (
                        f"Expected to find an array at {array_path}, "
                        "but a group was found there instead."
                    )
                    raise ValueError(msg) from e
                members_tree_flat["/" + dataset.path] = array_spec
        members_normalized = GroupSpec.from_flat(members_tree_flat)

        guess_inferred_members = guess.model_copy(
            update={"members": members_normalized.members}
        )
        return cls(**guess_inferred_members.model_dump())

    @classmethod
    def from_arrays(
        cls,
        arrays: Sequence[ArrayLike | ChunkedArrayLike],
        *,
        paths: Sequence[str],
        axes: Sequence[Axis],
        scales: Sequence[tuple[int | float, ...]],
        translations: Sequence[tuple[int | float, ...]],
        name: str | None = None,
        type: str | None = None,
        metadata: dict[str, Any] | None = None,
        chunks: tuple[int, ...]
        | tuple[tuple[int, ...], ...]
        | Literal["auto"] = "auto",
        compressor: Codec = DEFAULT_COMPRESSOR,
        fill_value: Any = 0,
        order: Literal["C", "F", "auto"] = "auto",
    ) -> Self:
        """
        Create a `Group` from a sequence of multiscale arrays and spatial metadata.

        The arrays are used as templates for corresponding `ArraySpec` instances, which model the Zarr arrays that would be created if the `Group` was stored.

        Parameters
        ----------
        paths: Sequence[str]
            The paths to the arrays.
        axes: Sequence[Axis]
            `Axis` objects describing the dimensions of the arrays.
        arrays: Sequence[ArrayLike] | Sequence[ChunkedArrayLike]
            A sequence of array-like objects that collectively represent the same image
            at multiple levels of detail. The attributes of these arrays are used to create `ArraySpec` objects
            that model Zarr arrays stored in the Zarr group.
        scales: Sequence[Sequence[int | float]]
            A scale value for each axis of the array, for each array in `arrays`.
        translations: Sequence[Sequence[int | float]]
            A translation value for each axis the array, for each array in `arrays`.
        name: str | None, default = None
            A name for the multiscale collection. Optional.
        type: str | None, default = None
            A description of the type of multiscale image represented by this group. Optional.
        metadata: Dict[str, Any] | None, default = None
            Arbitrary metadata associated with this multiscale collection. Optional.
        chunks: tuple[int] | tuple[tuple[int, ...]] | Literal["auto"], default = "auto"
            The chunks for the arrays in this multiscale group.
            If the string "auto" is provided, each array will have chunks set to the zarr-python default value, which depends on the shape and dtype of the array.
            If a single sequence of ints is provided, then this defines the chunks for all arrays.
            If a sequence of sequences of ints is provided, then this defines the chunks for each array.
        fill_value: Any, default = 0
            The fill value for the Zarr arrays.
        compressor: `Codec`
            The compressor to use for the arrays. Default is `numcodecs.ZStd`.
        order: "auto" | "C" | "F"
            The memory layout used for chunks of Zarr arrays. The default is "auto", which will infer the order from the input arrays, and fall back to "C" if that inference fails.
        """

        chunks_normalized = normalize_chunks(
            chunks,
            shapes=tuple(s.shape for s in arrays),
            typesizes=tuple(s.dtype.itemsize for s in arrays),
        )

        members_flat = {
            "/" + key.lstrip("/"): ArraySpec.from_array(
                array=arr,
                chunks=cnks,
                attributes={},
                compressor=compressor,
                filters=None,
                fill_value=fill_value,
                order=order,
            )
            for key, arr, cnks in zip(paths, arrays, chunks_normalized)
        }

        multimeta = MultiscaleMetadata(
            name=name,
            type=type,
            metadata=metadata,
            axes=tuple(axes),
            datasets=tuple(
                create_dataset(path=path, scale=scale, translation=translation)
                for path, scale, translation in zip(paths, scales, translations)
            ),
            coordinateTransformations=None,
        )
        return cls(
            members=GroupSpec.from_flat(members_flat).members,
            attributes=MultiscaleGroupAttrs(multiscales=(multimeta,)),
        )

    @model_validator(mode="after")
    def check_arrays_exist(self) -> MultiscaleGroup:
        """
        Check that the arrays referenced in the `multiscales` metadata are actually contained in this group.
        """
        attrs = self.attributes
        flattened = self.to_flat()

        for multiscale in attrs.multiscales:
            for dataset in multiscale.datasets:
                dpath = "/" + dataset.path.lstrip("/")
                if dpath in flattened:
                    if not isinstance(flattened[dpath], ArraySpec):
                        msg = (
                            f"The node at {dpath} should be an array, "
                            f"found {type(flattened[dpath])} instead"
                        )
                        raise ValueError(msg)
                else:
                    msg = (
                        f"Dataset {dataset.path} was specified in multiscale metadata, but no "
                        "array with that name was found in the hierarchy. "
                        "All arrays referenced in multiscale metadata must be contained in the group."
                    )
                    raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def check_array_ndim(self) -> MultiscaleGroup:
        """
        Check that all the arrays referenced by the `multiscales` metadata have dimensionality consistent with the
        `coordinateTransformations` metadata.
        """
        multimeta = self.attributes.multiscales

        flat_self = self.to_flat()

        # check that each transform has compatible rank
        for multiscale in multimeta:
            for dataset in multiscale.datasets:
                arr: ArraySpec = flat_self["/" + dataset.path.lstrip("/")]
                arr_ndim = len(arr.shape)
                tforms = dataset.coordinateTransformations

                if multiscale.coordinateTransformations is not None:
                    tforms += multiscale.coordinateTransformations

                for tform in tforms:
                    if hasattr(tform, "scale") or hasattr(tform, "translation"):
                        tform = cast(
                            tx.VectorScale | tx.VectorTranslation,
                            tform,
                        )
                        if (tform_ndim := tx.ndim(tform)) != arr_ndim:
                            msg = (
                                f"Transform {tform} has dimensionality {tform_ndim}, "
                                "which does not match the dimensionality of the array "
                                f"found in this group at {dataset.path} ({arr_ndim}). "
                                "Transform dimensionality must match array dimensionality."
                            )

                            raise ValueError(msg)

        return self


# for backwards compatibility
@deprecated(
    "The `Group` class has been renamed to `MultiscaleGroup`. This class remains for backwards compatibility, but it will be removed. You should use `MultiscaleGroup`."
)
class Group(MultiscaleGroup): ...


@deprecated(
    "The `GroupAttrs` class has been renamed to `MultiscaleGroupAttrs`. This class remains for backwards compatibility, but it will be removed. You should use `MultiscaleGroupAttrs`."
)
class GroupAttrs(MultiscaleGroupAttrs): ...


def normalize_chunks(
    chunks: Any,
    shapes: tuple[tuple[int, ...], ...],
    typesizes: tuple[int, ...],
) -> tuple[tuple[int, ...], ...]:
    """
    If chunks is "auto", then use zarr default chunking based on the largest array for all the arrays.
    If chunks is a sequence of ints, then use those chunks for all arrays.
    If chunks is a sequence of sequences of ints, then use those chunks for each array.
    """
    if chunks == "auto":
        # sort shapes by descending size
        params_sorted_descending = sorted(
            zip(shapes, typesizes), key=lambda v: np.prod(v[0]), reverse=True
        )
        return (guess_chunks(*params_sorted_descending[0]),) * len(shapes)
    if isinstance(chunks, Sequence):
        if all(isinstance(element, int) for element in chunks):
            return (tuple(chunks),) * len(shapes)
        if all(isinstance(element, Sequence) for element in chunks):
            if all(all(isinstance(k, int) for k in v) for v in chunks):
                return tuple(map(tuple, chunks))
            else:
                msg = f"Expected a sequence of sequences of ints. Got {chunks} instead."
                raise ValueError(msg)
    msg = f'Input must be a sequence or the string "auto". Got {type(chunks)}'
    raise TypeError(msg)
