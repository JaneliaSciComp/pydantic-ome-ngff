from __future__ import annotations

import jsonschema as jsc
import pytest
from pydantic import ValidationError
from pydantic_zarr.v2 import ArraySpec

from pydantic_ome_ngff.latest.axis import Axis
from pydantic_ome_ngff.latest.multiscale import (
    Dataset,
    Group,
    GroupAttrs,
    MultiscaleMetadata,
)
from pydantic_ome_ngff.latest.transform import (
    Transform,
    VectorScale,
    VectorTranslation,
)
from tests.conftest import fetch_schemas


@pytest.fixture
def multi_meta() -> MultiscaleMetadata:
    axes = [
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
                VectorScale(scale=(1,) * rank),
                VectorTranslation(translation=(0,) * rank),
            ),
        )
        for idx in range(num_datasets)
    ]

    multi = MultiscaleMetadata(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=(VectorScale(scale=(1,) * rank),),
    )
    return multi


def test_multiscale(multi_meta: MultiscaleMetadata) -> None:
    _, strict_schema = fetch_schemas("latest", schema_name="image")
    jsc.validate({"multiscales": [multi_meta.model_dump(mode="json")]}, strict_schema)


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
                VectorScale(scale=(1, 1, 1)),
                VectorTranslation(translation=(0, 0, 0)),
            ),
        )
    ]

    MultiscaleMetadata(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=(VectorScale(scale=(1, 1, 1)),),
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
                VectorScale(scale=(1, 1, 1)),
                VectorTranslation(translation=(0, 0, 0)),
            ),
        )
    ]

    with pytest.raises(ValidationError, match="Axis names must be unique."):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(VectorScale(scale=(1, 1, 1)),),
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
    axes: list[Axis] = []
    for idx, t in enumerate(axis_types):
        if t is None or t == "channel":
            ax = Axis(name=str(idx), type=t, unit=units_map.get(t))
        else:
            ax = Axis(name=str(idx), type=t, unit=units_map.get(t))
        axes.append(ax)

    rank = len(axes)
    datasets = [
        Dataset(
            path="path",
            coordinateTransformations=(
                VectorScale(scale=(1,) * rank),
                VectorTranslation(translation=(0,) * rank),
            ),
        )
    ]
    # TODO: make some axis-specifc exceptions
    with pytest.raises(ValidationError, match="Space axes must come last."):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(VectorScale(scale=(1,) * rank),),
        )


@pytest.mark.parametrize("num_axes", [0, 1, 6, 7])
def test_multiscale_axis_length(num_axes: int) -> None:
    rank = num_axes
    axes = [Axis(name=str(idx), type="space", unit="meter") for idx in range(num_axes)]
    datasets = [
        Dataset(
            path="path",
            coordinateTransformations=(
                VectorScale(scale=(1,) * rank),
                VectorTranslation(translation=(0,) * rank),
            ),
        )
    ]
    with pytest.raises(ValidationError, match="Incorrect number of axes provided"):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(VectorScale(scale=(1,) * rank),),
        )


def test_coordinate_transforms_invalid_ndims() -> None:
    tforms = [
        VectorScale(scale=(1, 1)),
        VectorTranslation(translation=(1, 1, 1)),
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
    transforms: tuple[Transform, Transform],
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
    transforms: tuple[Transform, Transform],
) -> None:
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary or instance of VectorTranslation",
    ):
        Dataset(path="foo", coordinateTransformations=transforms)


def test_multiscale_group_datasets_exist(
    multi_meta: MultiscaleMetadata,
) -> None:
    meta_ndim = len(multi_meta.axes)
    group_attrs = GroupAttrs(multiscales=[multi_meta])
    good_items = {
        d.path: ArraySpec(
            shape=(1,) * meta_ndim, dtype="uint8", chunks=(1,) * meta_ndim
        )
        for d in multi_meta.datasets
    }
    Group(attributes=group_attrs, members=good_items)

    bad_items = {
        d.path + "x": ArraySpec(
            shape=(1,) * meta_ndim, dtype="uint8", chunks=(1,) * meta_ndim
        )
        for d in multi_meta.datasets
    }

    with pytest.raises(
        ValidationError,
        match="array with that name was found in the hierarchy.",
    ):
        Group(attributes=group_attrs, members=bad_items)


def test_multiscale_group_datasets_rank(multi_meta: MultiscaleMetadata) -> None:
    meta_ndim = len(multi_meta.axes)
    group_attrs = GroupAttrs(multiscales=[multi_meta])
    good_items = {
        d.path: ArraySpec(
            shape=(1,) * meta_ndim, dtype="uint8", chunks=(1,) * meta_ndim
        )
        for d in multi_meta.datasets
    }
    Group(attributes=group_attrs, members=good_items)

    match = "Transform dimensionality must match array dimensionality."
    # arrays with varying rank
    bad_items = {
        d.path: ArraySpec(
            shape=(1,) * (idx + 1),
            dtype="uint8",
            chunks=(1,) * (idx + 1),
        )
        for idx, d in enumerate(multi_meta.datasets)
    }

    with pytest.raises(ValidationError, match=match):
        Group(attributes=group_attrs, members=bad_items)

    with pytest.raises(ValidationError, match=match):
        # arrays with rank that doesn't match the transform
        bad_items = {
            d.path: ArraySpec(
                shape=(1,),
                dtype="uint8",
                chunks=(1,),
            )
            for d in multi_meta.datasets
        }
        Group(attributes=group_attrs, members=bad_items)


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
                VectorScale(scale=(1,) * rank),
                VectorTranslation(translation=(0,) * rank),
            ),
        )
        for idx in range(num_datasets)
    ]

    multi = MultiscaleMetadata(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=(VectorScale(scale=(1,) * rank),),
    )
    return multi
