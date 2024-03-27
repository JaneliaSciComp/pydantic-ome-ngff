from __future__ import annotations
from typing import Dict, Literal, Tuple
from pydantic import ValidationError
import pytest
import jsonschema as jsc
from zarr.util import guess_chunks
from pydantic_zarr.v2 import ArraySpec
from pydantic_ome_ngff.v04.multiscale import (
    MultiscaleMetadata,
    GroupAttrs,
    Dataset,
    Group,
)

from pydantic_ome_ngff.v04.transform import (
    Transform,
    VectorScale,
    VectorTranslation,
)
from pydantic_ome_ngff.v04.axis import Axis
from tests.conftest import fetch_schemas
import numpy as np
from itertools import accumulate
import operator


@pytest.fixture
def default_multiscale() -> MultiscaleMetadata:
    axes = [
        Axis(name="c", type="channel", unit=None),
        Axis(name="z", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
        Axis(name="y", type="space", unit="meter"),
    ]
    rank = len(axes)
    num_datasets = 3
    datasets = [
        Dataset(
            path=f"path{idx}",
            coordinateTransformations=(
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
                VectorTranslation(
                    translation=[
                        0,
                    ]
                    * rank
                ),
            ),
        )
        for idx in range(num_datasets)
    ]

    multi = MultiscaleMetadata(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=(
            VectorScale(
                scale=[
                    1,
                ]
                * rank
            ),
        ),
    )
    return multi


def test_multiscale(default_multiscale: MultiscaleMetadata) -> None:
    base_schema, strict_schema = fetch_schemas("0.4", schema_name="image")
    jsc.validate(
        {"multiscales": [default_multiscale.model_dump(mode="json")]}, strict_schema
    )


def test_multiscale_unique_axis_names() -> None:
    axes = [
        Axis(name="y", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]

    # this should be fine

    datasets = [
        Dataset(
            path="path",
            coordinateTransformations=(
                VectorScale(scale=[1, 1, 1]),
                VectorTranslation(translation=[0, 0, 0]),
            ),
        )
    ]

    MultiscaleMetadata(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=(VectorScale(scale=[1, 1, 1]),),
    )

    # make axis names collide
    axes = [
        Axis(name="x", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]
    datasets = [
        Dataset(
            path="path",
            coordinateTransformations=(
                VectorScale(scale=[1, 1]),
                VectorTranslation(translation=[0, 0]),
            ),
        )
    ]

    with pytest.raises(ValidationError, match="Axis names must be unique."):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(VectorScale(scale=[1, 1]),),
        )


@pytest.mark.parametrize(
    "axis_types",
    [
        ("space", "space", "channel"),
        ("space", "channel", "space", "channel"),
    ],
)
def test_multiscale_space_axes_last(axis_types: list[str | None]) -> None:
    units_map = {"space": "meter", "time": "second"}
    axes = [
        Axis(name=str(idx), type=t, unit=units_map.get(t, None))
        for idx, t in enumerate(axis_types)
    ]
    rank = len(axes)
    datasets = [
        Dataset(
            path="path",
            coordinateTransformations=(
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
                VectorTranslation(
                    translation=[
                        0,
                    ]
                    * rank
                ),
            ),
        )
    ]
    # TODO: make some axis-specifc exceptions
    with pytest.raises(ValidationError, match="Space axes must come last."):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
            ),
        )


@pytest.mark.parametrize("num_axes", [0, 1, 6, 7])
def test_multiscale_axis_length(num_axes: int) -> None:
    rank = num_axes
    axes = [Axis(name=str(idx), type="space", unit="meter") for idx in range(num_axes)]
    datasets = [
        Dataset(
            path="path",
            coordinateTransformations=(
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
                VectorTranslation(
                    translation=[
                        0,
                    ]
                    * rank
                ),
            ),
        )
    ]
    with pytest.raises(ValidationError, match="Incorrect number of axes provided"):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
            ),
        )


@pytest.mark.parametrize(
    "scale, translation", [((1, 1), (1, 1, 1)), ((1, 1, 1), (1, 1))]
)
def test_coordinate_transforms_invalid_ndims(
    scale: tuple[int, ...], translation: tuple[int, ...]
) -> None:
    tforms = [
        VectorScale(scale=scale),
        VectorTranslation(translation=translation),
    ]
    with pytest.raises(
        ValidationError,
        match="The transforms have inconsistent dimensionality.",
    ):
        Dataset(path="foo", coordinateTransformations=tforms)


@pytest.mark.parametrize(
    "transforms",
    [
        [
            VectorScale(scale=(1, 1, 1)),
            VectorTranslation(translation=(1, 1, 1)),
            VectorTranslation(translation=(1, 1, 1)),
        ],
        [
            VectorScale(scale=(1, 1, 1)),
        ]
        * 5,
    ],
)
def test_coordinate_transforms_invalid_length(
    transforms: list[Transform],
) -> None:
    with pytest.raises(
        ValidationError, match=f"after validation, not {len(transforms)}"
    ):
        Dataset(path="foo", coordinateTransformations=transforms)


@pytest.mark.parametrize(
    "transforms",
    [
        [
            VectorTranslation(translation=(1, 1, 1)),
        ]
        * 2,
        [
            VectorTranslation(translation=(1, 1, 1)),
            VectorScale(scale=(1, 1, 1)),
        ],
    ],
)
def test_coordinate_transforms_invalid_first_element(
    transforms: Tuple[Transform, Transform],
) -> None:
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary or instance of VectorScale",
    ):
        Dataset(path="foo", coordinateTransformations=transforms)


@pytest.mark.parametrize(
    "transforms",
    (
        [
            VectorScale(scale=(1, 1, 1)),
            VectorScale(scale=(1, 1, 1)),
        ],
    ),
)
def test_coordinate_transforms_invalid_second_element(
    transforms: Tuple[VectorScale, VectorScale],
) -> None:
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary or instance of VectorTranslation",
    ):
        Dataset(path="foo", coordinateTransformations=transforms)


def test_multiscale_group_datasets_exist(
    default_multiscale: MultiscaleMetadata,
) -> None:
    group_attrs = GroupAttrs(multiscales=[default_multiscale])
    good_items = {
        d.path: ArraySpec(
            shape=(1, 1, 1, 1),
            dtype="uint8",
            chunks=(1, 1, 1, 1),
        )
        for d in default_multiscale.datasets
    }
    Group(attributes=group_attrs, members=good_items)

    bad_items = {
        d.path + "x": ArraySpec(
            shape=(1, 1, 1, 1),
            dtype="uint8",
            chunks=(1, 1, 1, 1),
        )
        for d in default_multiscale.datasets
    }

    with pytest.raises(
        ValidationError,
        match="array with that name was found in the hierarchy",
    ):
        bad_items = {
            d.path + "x": ArraySpec(
                shape=(1, 1, 1, 1),
                dtype="uint8",
                chunks=(1, 1, 1, 1),
            )
            for d in default_multiscale.datasets
        }
        Group(attributes=group_attrs, members=bad_items)


def test_multiscale_group_datasets_rank(default_multiscale: MultiscaleMetadata) -> None:
    group_attrs = GroupAttrs(multiscales=[default_multiscale])
    good_items = {
        d.path: ArraySpec(
            shape=(1, 1, 1, 1),
            dtype="uint8",
            chunks=(1, 1, 1, 1),
        )
        for d in default_multiscale.datasets
    }
    Group(attributes=group_attrs, members=good_items)

    # arrays with varying rank
    bad_items = {
        d.path: ArraySpec(
            shape=(1,) * (idx + 1),
            dtype="uint8",
            chunks=(1,) * (idx + 1),
        )
        for idx, d in enumerate(default_multiscale.datasets)
    }
    match = "Transform dimensionality must match array dimensionality."
    with pytest.raises(ValidationError, match=match):
        # arrays with varying rank
        bad_items = {
            d.path: ArraySpec(
                shape=(1,) * (idx + 1),
                dtype="uint8",
                chunks=(1,) * (idx + 1),
            )
            for idx, d in enumerate(default_multiscale.datasets)
        }
        Group(attributes=group_attrs, members=bad_items)

    # arrays with rank that doesn't match the transform
    bad_items = {
        d.path: ArraySpec(shape=(1,), dtype="uint8", chunks=(1,))
        for d in default_multiscale.datasets
    }
    with pytest.raises(ValidationError, match=match):
        # arrays with rank that doesn't match the transform
        bad_items = {
            d.path: ArraySpec(shape=(1,), dtype="uint8", chunks=(1,))
            for d in default_multiscale.datasets
        }
        Group(attributes=group_attrs, members=bad_items)


@pytest.mark.parametrize("name", [None, "foo"])
@pytest.mark.parametrize("type", [None, "foo"])
@pytest.mark.parametrize("path_pattern", ["{0}", "s{0}", "foo/{0}"])
@pytest.mark.parametrize("metadata", [None, {"foo": 10}])
@pytest.mark.parametrize("ndim", [2, 3, 4, 5])
@pytest.mark.parametrize("chunks", ["auto", "tuple", "tuple-of-tuple"])
@pytest.mark.parametrize("order", ["auto", "C", "F"])
def test_from_arrays(
    name: str | None,
    type: str | None,
    path_pattern: str,
    metadata: Dict[str, int] | None,
    ndim: int,
    chunks: Literal["auto", "tuple", "tuple-of-tuple"],
    order: Literal["auto", "C", "F"],
) -> None:
    arrays = [np.arange(x**ndim).reshape((x,) * ndim) for x in [3, 2, 1]]
    paths = [path_pattern.format(idx) for idx in range(len(arrays))]
    scales = [(2**idx,) * ndim for idx in range(len(arrays))]
    translations = [
        (t,) * ndim
        for t in accumulate(
            [(2 ** (idx - 1)) for idx in range(len(arrays))], operator.add
        )
    ]

    all_axes = [
        Axis(
            name="x",
            type="space",
        ),
        Axis(name="y", type="space"),
        Axis(name="z", type="space"),
        Axis(name="t", type="time"),
        Axis(name="c", type="barf"),
    ]
    # spatial axes have to come last
    if ndim in (2, 3):
        axes = all_axes[:ndim]
    else:
        axes = [*all_axes[4:], *all_axes[:3]]

    if chunks == "auto":
        chunks_arg = chunks
        chunks_expected = (
            guess_chunks(arrays[0].shape, arrays[0].dtype.itemsize),
        ) * len(arrays)
    elif chunks == "tuple":
        chunks_arg = (2,) * ndim
        chunks_expected = (chunks_arg,) * len(arrays)
    elif chunks == "tuple-of-tuple":
        chunks_arg = tuple((idx,) * ndim for idx in range(1, len(arrays) + 1))
        chunks_expected = chunks_arg

    if order == "auto":
        order_expected = "C"
    else:
        order_expected = order

    group = Group.from_arrays(
        paths=paths,
        axes=axes,
        arrays=arrays,
        scales=scales,
        translations=translations,
        name=name,
        type=type,
        metadata=metadata,
        chunks=chunks_arg,
        order=order,
    )

    group_flat = group.to_flat()

    assert group.attributes.multiscales[0].name == name
    assert group.attributes.multiscales[0].type == type
    assert group.attributes.multiscales[0].metadata == metadata
    assert group.attributes.multiscales[0].coordinateTransformations is None
    assert group.attributes.multiscales[0].axes == tuple(axes)
    for idx, array in enumerate(arrays):
        array_model: ArraySpec = group_flat["/" + paths[idx]]
        assert array_model.order == order_expected
        assert array.shape == array_model.shape
        assert array.dtype == array_model.dtype
        assert chunks_expected[idx] == array_model.chunks
        assert group.attributes.multiscales[0].datasets[
            idx
        ].coordinateTransformations == (
            VectorScale(scale=scales[idx]),
            VectorTranslation(translation=translations[idx]),
        )
