from __future__ import annotations

from typing import Iterable, cast, overload

from pydantic_ome_ngff.v04.multiscale import Dataset, MultiscaleMetadata
from pydantic_ome_ngff.v04.transform import VectorScale, VectorTranslation


@overload
def transform(metadata: Dataset) -> Dataset:
    ...


@overload
def transform(metadata: MultiscaleMetadata) -> MultiscaleMetadata:
    ...


def transform(
    metadata: Dataset | MultiscaleMetadata,
    *,
    scale: Iterable[float] | None = None,
    translation: Iterable[float] | None = None,
) -> Dataset | MultiscaleMetadata:
    """
    Apply a spatial transformation to all the coordinate transformations in multiscale metadata.
    """

    if isinstance(metadata, Dataset):
        return transform_dataset(metadata, scale=scale, translation=translation)

    return transform_multiscale(metadata, scale=scale, translation=translation)


def transform_dataset(
    metadata: Dataset,
    *,
    scale: Iterable[float] | None = None,
    translation: Iterable[float] | None = None,
) -> Dataset:
    new_transforms = transform_coordinate_transformations(
        metadata.coordinateTransformations, scale=scale, translation=translation
    )
    return Dataset(path=metadata.path, coordinateTransformations=new_transforms)


def transform_coordinate_transformations(
    metadata: tuple[VectorScale] | tuple[VectorScale, VectorTranslation],
    scale: Iterable[float] | None = None,
    translation: Iterable[float] | None = None,
) -> tuple[VectorScale] | tuple[VectorScale, VectorTranslation]:
    new_transforms: tuple[VectorScale] | tuple[VectorScale, VectorTranslation]
    ndim = metadata[0].ndim
    old_scale_param = metadata[0].scale
    in_scale_param_norm = normalize_scale(ndim, param=scale)
    new_scale_param = tuple(a * b for a, b in zip(in_scale_param_norm, old_scale_param))
    new_transforms = (VectorScale(scale=new_scale_param),)

    if translation is not None:
        if len(metadata) == 1:
            old_trans_param = normalize_translation(ndim, param=None)
        elif len(metadata) == 2:
            old_trans_param = metadata[1].translation
        else:
            raise AssertionError
        in_trans_param_norm = normalize_translation(ndim, param=translation)
        new_trans_param = tuple(
            a + b for a, b in zip(in_trans_param_norm, old_trans_param)
        )
        new_transforms += (VectorTranslation(translation=new_trans_param),)
    elif len(metadata) == 2:
        new_transforms += (metadata[1],)

    return new_transforms


def transform_multiscale(
    metadata: MultiscaleMetadata,
    *,
    scale: Iterable[float] | None = None,
    translation: Iterable[float] | None = None,
) -> MultiscaleMetadata:
    # Consider adding a flag to target the coordinateTransformations attribute of MultiscaleMetadata,
    # or the coordinateTransformations attribute of the datasets

    new_datasets = tuple(
        transform_dataset(dataset, scale=scale, translation=translation)
        for dataset in metadata.datasets
    )

    model_dict = metadata.model_dump(exclude={"datasets"})

    return MultiscaleMetadata(
        **model_dict,
        datasets=new_datasets,
    )


def normalize_translation(
    ndim: int, param: Iterable[float] | None
) -> tuple[float, ...]:
    if param is None:
        return (0,) * ndim

    return tuple(param)


def normalize_scale(ndim: int, param: Iterable[float] | None) -> tuple[float, ...]:
    if param is None:
        return (1,) * ndim

    return tuple(param)


@overload
def transpose_axes_coordinate_transforms(
    metadata: tuple[VectorScale],
    axis_order: Iterable[int],
) -> tuple[VectorScale]:
    ...


@overload
def transpose_axes_coordinate_transforms(
    metadata: tuple[VectorScale, VectorTranslation],
    axis_order: Iterable[int],
) -> tuple[VectorScale, VectorTranslation]:
    ...


def transpose_axes_coordinate_transforms(
    metadata: tuple[VectorScale] | tuple[VectorScale, VectorTranslation],
    axis_order: Iterable[int],
) -> tuple[VectorScale] | tuple[VectorScale, VectorTranslation]:
    transforms_out: tuple[VectorScale] | tuple[VectorScale, VectorTranslation] = ()

    order_tuple = tuple(axis_order)

    if len(set(order_tuple)) != len(order_tuple):
        msg = f"Axis order {order_tuple} contains repeated values."
        raise ValueError(msg)

    for tx in metadata:
        if isinstance(tx, VectorScale):
            new_scale = tuple(tx.scale[idx] for idx in order_tuple)
            new_tx = VectorScale(scale=new_scale)
        elif isinstance(tx, VectorTranslation):
            new_trans = tuple(tx.translation[idx] for idx in order_tuple)
            new_tx = VectorTranslation(translation=new_trans)
        else:
            msg = f"Cannot tranpose instances of {type(tx)}"
            raise TypeError(msg)
        transforms_out += (new_tx,)

    return transforms_out


def transpose_axes_dataset(metadata: Dataset, axis_order: Iterable[int]) -> Dataset:
    transforms_reordered = transpose_axes_coordinate_transforms(
        metadata.coordinateTransformations,
        axis_order=axis_order,
    )
    return Dataset(path=metadata.path, coordinateTransformations=transforms_reordered)


def transpose_axes_multiscale(
    metadata: MultiscaleMetadata, axis_order: Iterable[int] | Iterable[str]
) -> MultiscaleMetadata:
    order_tuple = tuple(axis_order)
    old_axes_dict = {ax.name: ax for ax in metadata.axes}
    keys_tuple = tuple(old_axes_dict.keys())

    if all(isinstance(x, str) for x in axis_order):
        axis_order_int = tuple(keys_tuple.index(ax) for ax in axis_order)
    elif all(isinstance(x, int) for x in axis_order):
        axis_order = cast(Iterable[int], axis_order)
        axis_order_int = tuple(axis_order)
    else:
        msg = "All elements of axis_order must be str or int."
        raise TypeError(msg)

    if len(set(axis_order_int)) != len(axis_order_int):
        msg = f"Axis order {order_tuple} contains repeated values."
        raise ValueError(msg)

    if len(axis_order_int) != len(metadata.axes):
        msg = (
            f"Number of elements in axis_order ({len(axis_order_int)}) "
            f"differs from the number of axes ({len(metadata.axes)}) "
        )
        raise ValueError(msg)

    new_axes = tuple(metadata.axes[idx] for idx in axis_order_int)
    new_datasets = tuple(
        transpose_axes_dataset(d, axis_order=axis_order_int) for d in metadata.datasets
    )
    if metadata.coordinateTransformations is not None:
        new_ctx = transpose_axes_coordinate_transforms(
            metadata.coordinateTransformations, axis_order=axis_order_int
        )
    else:
        new_ctx = None

    return MultiscaleMetadata(
        axes=new_axes,
        datasets=new_datasets,
        coordinateTransformations=new_ctx,
        **metadata.model_dump(
            exclude={"axes", "datasets", "coordinateTransformations"}
        ),
    )


@overload
def transpose_axes(metadata: Dataset, axis_order: Iterable[int]) -> Dataset:
    ...


@overload
def transpose_axes(
    metadata: MultiscaleMetadata, axis_order: Iterable[int] | Iterable[str]
) -> MultiscaleMetadata:
    ...


def transpose_axes(
    metadata: MultiscaleMetadata | Dataset, axis_order: Iterable[int] | Iterable[str]
) -> MultiscaleMetadata | Dataset:
    if isinstance(metadata, Dataset):
        if all(isinstance(x, int) for x in axis_order):
            axis_order = cast(Iterable[int], axis_order)
            return transpose_axes_dataset(metadata, axis_order=axis_order)

        msg = "To transpose a Dataset, all elements of axis_order must be ints."
        raise TypeError(msg)

    return transpose_axes_multiscale(metadata, axis_order=axis_order)
