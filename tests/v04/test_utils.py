from __future__ import annotations

import pytest
from typing_extensions import Literal

from pydantic_ome_ngff.v04.axis import Axis
from pydantic_ome_ngff.v04.multiscale import Dataset, MultiscaleMetadata
from pydantic_ome_ngff.v04.transform import VectorScale, VectorTranslation
from pydantic_ome_ngff.v04.utils import (
    normalize_scale,
    normalize_translation,
    transform_coordinate_transformations,
    transform_dataset,
    transform_multiscale,
    transpose_axes_coordinate_transforms,
    transpose_axes_dataset,
    transpose_axes_multiscale,
)


@pytest.mark.parametrize(
    "ndim, scale", ((3, (1, 2, 3)), (3, None), (2, (1, 2)), (2, None))
)
def test_normalize_scale(ndim: int, scale: tuple[int, int, int] | None) -> None:
    normalized = normalize_scale(ndim=ndim, param=scale)
    if scale is None:
        assert normalized == (1,) * ndim
    else:
        assert normalized == scale


@pytest.mark.parametrize(
    "ndim, trans", ((3, (1, 2, 3)), (3, None), (2, (1, 2)), (2, None))
)
def test_normalize_translation(ndim: int, trans: tuple[int, int, int] | None) -> None:
    normalized = normalize_translation(ndim=ndim, param=trans)
    if trans is None:
        assert normalized == (0,) * ndim
    else:
        assert normalized == trans


@pytest.mark.parametrize("ndim", (1, 2, 3))
@pytest.mark.parametrize("old_trans", (None, "auto"))
@pytest.mark.parametrize("in_scale", (None, "auto"))
@pytest.mark.parametrize("in_trans", (None, "auto"))
def test_transform_coordinate_transformations(
    ndim: int,
    old_trans: Literal["auto"] | None,
    in_scale: Literal["auto"] | None,
    in_trans: Literal["auto"] | None,
) -> None:
    old_ctx: tuple[VectorScale] | tuple[VectorScale, VectorTranslation] = ()
    old_scale = tuple(range(ndim))
    old_ctx += (VectorScale(scale=old_scale),)

    if old_trans is None:
        old_trans_norm = (0,) * ndim
    else:
        old_trans_norm = tuple(range(2, ndim + 2))
        old_ctx += (VectorTranslation(translation=old_trans_norm),)

    if in_scale == "auto":
        _new_scale = (2,) * ndim
    else:
        _new_scale = None

    if in_trans == "auto":
        _new_trans = (1.5,) * ndim
    else:
        _new_trans = None

    new_ctx = transform_coordinate_transformations(
        old_ctx, scale=_new_scale, translation=_new_trans
    )

    if old_trans is None:
        if in_trans is None:
            assert len(new_ctx) == 1
        else:
            assert len(new_ctx) == 2
    elif in_trans is None:
        assert new_ctx[1] == old_ctx[1]
    else:
        assert new_ctx[1] == VectorTranslation(
            translation=tuple(a + b for a, b in zip(old_trans_norm, _new_trans))
        )
    if _new_scale is None:
        assert new_ctx[0] == old_ctx[0]
    else:
        assert new_ctx[0] == VectorScale(
            scale=tuple(a * b for a, b in zip(old_scale, _new_scale))
        )


@pytest.mark.parametrize("old_trans", (None, (2, 2)))
@pytest.mark.parametrize("in_scale", (None, (1, 1), (2, 3)))
@pytest.mark.parametrize("in_trans", (None, (0, 0), (1, 1)))
def test_transform_dataset(
    old_trans: tuple[int, int] | None,
    in_scale: tuple[int, int] | None,
    in_trans: tuple[int, int] | None,
) -> None:
    base_coords = (VectorScale(scale=(2, 2)),)
    scale_norm = normalize_scale(ndim=2, param=in_scale)
    trans_norm = normalize_translation(2, param=in_trans)
    if old_trans is not None:
        base_coords += (VectorTranslation(translation=old_trans),)

    old_dataset = Dataset(path="foo", coordinateTransformations=base_coords)
    new_dataset = transform_dataset(old_dataset, scale=in_scale, translation=in_trans)
    exclude = {"coordinateTransformations"}
    new_base_dict = new_dataset.model_dump(exclude=exclude)
    old_base_dict = old_dataset.model_dump(exclude=exclude)

    assert new_base_dict == old_base_dict
    new_ctx = new_dataset.coordinateTransformations
    old_ctx = old_dataset.coordinateTransformations
    scale_expected = tuple(a * b for a, b in zip(old_ctx[0].scale, scale_norm))
    scale_observed = new_ctx[0].scale

    assert scale_expected == scale_observed

    if in_trans is not None:
        if old_trans is None:
            old_trans_norm = (0, 0)
        else:
            old_trans_norm = old_ctx[1].translation
        trans_expected = tuple(a + b for a, b in zip(old_trans_norm, trans_norm))
        assert new_ctx[1].translation == trans_expected
    if old_trans is None and in_trans is None:
        assert len(new_ctx) == 1


@pytest.mark.parametrize(
    "ctx",
    (
        (
            None,
            (VectorScale(scale=(1, 2)),),
            (
                VectorScale(scale=(1, 2)),
                VectorTranslation(translation=(0.5, 0.5)),
            ),
        )
    ),
)
def test_transform_multiscale_metadata(
    ctx: None | tuple[VectorScale] | tuple[VectorScale, VectorTranslation],
) -> None:
    scale = (2, 2)
    trans = (0.5, 0.5)
    datasets = (
        Dataset(path="array_1", coordinateTransformations=(VectorScale(scale=(2, 2)),)),
    )
    old_meta = MultiscaleMetadata(
        axes=[{"name": "foo", "type": "space"}, {"name": "bar", "type": "space"}],
        datasets=datasets,
        coordinateTransformations=ctx,
    )

    new_meta = transform_multiscale(old_meta, scale=scale, translation=trans)
    for old_dataset, new_dataset in zip(datasets, new_meta.datasets):
        assert new_dataset == transform_dataset(
            old_dataset, scale=scale, translation=trans
        )


@pytest.mark.parametrize(
    "order", ((0, 1, 2), (0, 2, 1), ("x", "y", "z"), ("y", "x", "z"))
)
@pytest.mark.parametrize("ctx", (None, "auto"))
def test_transpose_axes_multiscale(
    order: tuple[int, ...] | tuple[str, ...], ctx: Literal["auto"] | None
) -> None:
    axes = {k: Axis(type="space", name=k) for k in ("x", "y", "z")}
    axes_tuple = tuple(axes.values())
    dataset = Dataset(
        path="foo",
        coordinateTransformations=(
            VectorScale(scale=(1, 2, 3)),
            VectorTranslation(translation=(2, 3, 4)),
        ),
    )

    if all(isinstance(a, str) for a in order):
        axis_order_int = tuple(tuple(axes.keys()).index(idx) for idx in order)
    else:
        axis_order_int = order

    if ctx is None:
        coordinate_transformations = None
    else:
        coordinate_transformations = (VectorScale(scale=(3, 4, 5)),)

    old_metadata = MultiscaleMetadata(
        axes=axes_tuple,
        datasets=(dataset,),
        coordinateTransformations=coordinate_transformations,
    )
    new_metadata = transpose_axes_multiscale(old_metadata, axis_order=order)
    exclude = {"axes", "datasets", "coordinateTransformations"}
    assert old_metadata.model_dump(exclude=exclude) == new_metadata.model_dump(
        exclude=exclude
    )
    new_ctx = new_metadata.coordinateTransformations
    old_ctx = old_metadata.coordinateTransformations
    if ctx is not None:
        assert new_ctx == transpose_axes_coordinate_transforms(
            old_ctx, axis_order=axis_order_int
        )
    else:
        assert new_ctx == old_ctx
    assert all(
        new_d == transpose_axes_dataset(old_d, axis_order=axis_order_int)
        for new_d, old_d in zip(old_metadata.datasets, new_metadata.datasets)
    )


@pytest.mark.parametrize(
    "order",
    (
        (0, 1, 2),
        (0, 2, 1),
    ),
)
def test_transpose_axes_dataset(order: tuple[int, int, int]) -> None:
    dataset = Dataset(
        path="foo",
        coordinateTransformations=(
            VectorScale(scale=(1, 2, 3)),
            VectorTranslation(translation=(2, 3, 4)),
        ),
    )

    transposed = transpose_axes_dataset(dataset, axis_order=order)
    scale_expected = tuple(
        dataset.coordinateTransformations[0].scale[idx] for idx in order
    )
    trans_expected = tuple(
        dataset.coordinateTransformations[1].translation[idx] for idx in order
    )
    assert transposed.coordinateTransformations[0].scale == scale_expected
    assert transposed.coordinateTransformations[1].translation == trans_expected
