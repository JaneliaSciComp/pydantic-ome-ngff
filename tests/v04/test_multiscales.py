from __future__ import annotations
from typing import List, Optional, Tuple
from pydantic import ValidationError
import pytest
import jsonschema as jsc
from pydantic_zarr.v2 import ArraySpec
from pydantic_ome_ngff.v04.multiscales import (
    Multiscale,
    MultiscaleAttrs,
    MultiscaleDataset,
    MultiscaleGroup,
)

from pydantic_ome_ngff.v04.transforms import (
    Transform,
    VectorScale,
    VectorTranslation,
)
from pydantic_ome_ngff.v04.axis import Axis
from tests.conftest import fetch_schemas


@pytest.fixture
def default_multiscale() -> Multiscale:
    axes = [
        Axis(name="c", type="channel", unit=None),
        Axis(name="z", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
        Axis(name="y", type="space", unit="meter"),
    ]
    rank = len(axes)
    num_datasets = 3
    datasets = [
        MultiscaleDataset(
            path=f"path{idx}",
            coordinateTransformations=[
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
            ],
        )
        for idx in range(num_datasets)
    ]

    multi = Multiscale(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=[
            VectorScale(
                scale=[
                    1,
                ]
                * rank
            ),
        ],
    )
    return multi


def test_multiscale(default_multiscale: Multiscale) -> None:
    base_schema, strict_schema = fetch_schemas("0.4", schema_name="image")
    jsc.validate({"multiscales": [default_multiscale.model_dump()]}, strict_schema)


def test_multiscale_unique_axis_names() -> None:
    axes = [
        Axis(name="y", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]

    # this should be fine

    datasets = [
        MultiscaleDataset(
            path="path",
            coordinateTransformations=[
                VectorScale(scale=[1, 1, 1]),
                VectorTranslation(translation=[0, 0, 0]),
            ],
        )
    ]

    Multiscale(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=[
            VectorScale(scale=[1, 1, 1]),
        ],
    )

    # make axis names collide
    axes = [
        Axis(name="x", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]
    datasets = [
        MultiscaleDataset(
            path="path",
            coordinateTransformations=[
                VectorScale(scale=[1, 1, 1]),
                VectorTranslation(translation=[0, 0, 0]),
            ],
        )
    ]

    with pytest.raises(ValidationError, match="Axis names must be unique."):
        Multiscale(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=[
                VectorScale(scale=[1, 1, 1]),
            ],
        )


@pytest.mark.parametrize(
    "axis_types",
    (
        ("space", "space", "channel"),
        ("space", "channel", "space", "channel"),
    ),
)
def test_multiscale_space_axes_last(axis_types: List[Optional[str]]) -> None:
    units_map = {"space": "meter", "time": "second"}
    axes = [
        Axis(name=str(idx), type=t, unit=units_map.get(t, None))
        for idx, t in enumerate(axis_types)
    ]
    rank = len(axes)
    datasets = [
        MultiscaleDataset(
            path="path",
            coordinateTransformations=[
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
            ],
        )
    ]
    # TODO: make some axis-specifc exceptions
    with pytest.raises(ValidationError, match="Space axes must come last."):
        Multiscale(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=[
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
            ],
        )


@pytest.mark.parametrize("num_axes", (0, 1, 6, 7))
def test_multiscale_axis_length(num_axes: int) -> None:
    rank = num_axes
    axes = [Axis(name=str(idx), type="space", unit="meter") for idx in range(num_axes)]
    datasets = [
        MultiscaleDataset(
            path="path",
            coordinateTransformations=[
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
            ],
        )
    ]
    with pytest.raises(ValidationError, match="Incorrect number of axes provided"):
        Multiscale(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=[
                VectorScale(
                    scale=[
                        1,
                    ]
                    * rank
                ),
            ],
        )


def test_coordinate_transforms_invalid_ndims() -> None:
    tforms = [
        VectorScale(scale=(1, 1)),
        VectorTranslation(translation=(1, 1, 1)),
    ]
    with pytest.raises(
        ValidationError,
        match="The transforms have inconsistent dimensionality.",  # noqa
    ):
        MultiscaleDataset(path="foo", coordinateTransformations=tforms)


@pytest.mark.parametrize(
    "transforms",
    (
        [
            VectorScale(scale=(1, 1, 1)),
            VectorTranslation(translation=(1, 1, 1)),
            VectorTranslation(translation=(1, 1, 1)),
        ],
        [
            VectorScale(scale=(1, 1, 1)),
        ]
        * 5,
    ),
)
def test_coordinate_transforms_invalid_length(
    transforms: List[Transform],
) -> None:
    with pytest.raises(ValidationError, match="expected 1 or 2"):
        MultiscaleDataset(path="foo", coordinateTransformations=transforms)


@pytest.mark.parametrize(
    "transforms",
    (
        [
            VectorTranslation(translation=(1, 1, 1)),
        ]
        * 2,
        [
            VectorTranslation(translation=(1, 1, 1)),
            VectorScale(scale=(1, 1, 1)),
        ],
    ),
)
def test_coordinate_transforms_invalid_first_element(
    transforms: Tuple[Transform, Transform],
) -> None:
    with pytest.raises(
        ValidationError,
        match="The first element of `coordinateTransformations` must be a",
    ):
        MultiscaleDataset(path="foo", coordinateTransformations=transforms)


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
    transforms: Tuple[Transform, Transform],
) -> None:
    with pytest.raises(
        ValidationError,
        match="The second element of `coordinateTransformations` must be a",
    ):
        MultiscaleDataset(path="foo", coordinateTransformations=transforms)


def test_multiscale_group_datasets_exist(default_multiscale: Multiscale) -> None:
    group_attrs = MultiscaleAttrs(multiscales=[default_multiscale])
    good_items = {
        d.path: ArraySpec(
            shape=(1, 1, 1, 1), dtype="uint8", chunks=(1, 1, 1, 1), attributes={}
        )
        for d in default_multiscale.datasets
    }
    MultiscaleGroup(attributes=group_attrs, members=good_items)

    with pytest.raises(
        ValidationError,
        match="array with that name was found in the items of that group.",
    ):
        bad_items = {
            d.path + "x": ArraySpec(
                shape=(1, 1, 1, 1), dtype="uint8", chunks=(1, 1, 1, 1), attributes={}
            )
            for d in default_multiscale.datasets
        }
        MultiscaleGroup(attributes=group_attrs, members=bad_items)


def test_multiscale_group_datasets_rank(default_multiscale: Multiscale) -> None:
    group_attrs = MultiscaleAttrs(multiscales=[default_multiscale])
    good_items = {
        d.path: ArraySpec(
            shape=(1, 1, 1, 1), dtype="uint8", chunks=(1, 1, 1, 1), attributes={}
        )
        for d in default_multiscale.datasets
    }
    MultiscaleGroup(attributes=group_attrs, members=good_items)

    with pytest.raises(
        ValidationError, match="All arrays must have the same dimensionality."
    ):
        # arrays with varying rank
        bad_items = {
            d.path: ArraySpec(
                shape=(1,) * (idx + 1),
                dtype="uint8",
                chunks=(1,) * (idx + 1),
                attributes={},
            )
            for idx, d in enumerate(default_multiscale.datasets)
        }
        MultiscaleGroup(attributes=group_attrs, members=bad_items)

    with pytest.raises(ValidationError, match="Transform dimensionality"):
        # arrays with rank that doesn't match the transform
        bad_items = {
            d.path: ArraySpec(shape=(1,), dtype="uint8", chunks=(1,), attributes={})
            for d in default_multiscale.datasets
        }
        MultiscaleGroup(attributes=group_attrs, members=bad_items)
