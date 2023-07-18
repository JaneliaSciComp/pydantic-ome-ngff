from typing import Tuple, List, Optional
import jsonschema as jsc
import pytest
from pydantic import ValidationError
from pydantic_ome_ngff.tree import Array
from .conftest import fetch_schemas
from pydantic_ome_ngff.v04.multiscales import (
    Multiscale,
    MultiscaleDataset,
    MultiscaleGroup,
)
from pydantic_ome_ngff.v04.coordinateTransformations import (
    CoordinateTransform,
    Transforms,
    VectorScaleTransform,
    VectorTranslationTransform,
)
from pydantic_ome_ngff.v04.axes import Axis


@pytest.fixture
def default_multiscale():
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
                VectorScaleTransform(
                    scale=[
                        1,
                    ]
                    * rank
                ),
                VectorTranslationTransform(
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
            VectorScaleTransform(
                scale=[
                    1,
                ]
                * rank
            ),
        ],
    )
    return multi


def test_multiscale_schema(default_multiscale):
    base_schema, strict_schema = fetch_schemas("0.4", schema_name="image")
    jsc.validate({"multiscales": [default_multiscale.dict()]}, strict_schema)
    jsc.validate({"multiscales": [default_multiscale.dict()]}, base_schema)


def test_multiscale_unique_axis_names():

    axes = [
        Axis(name="y", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]

    scale, trans = [
        VectorScaleTransform(scale=[1, 1]),
        VectorTranslationTransform(translation=[0, 0]),
    ]

    datasets = MultiscaleDataset(path="a", coordinateTransformations=[scale, trans])
    # this validates
    Multiscale(
        name="a", axes=axes, datasets=[datasets], coordinateTransformations=[scale]
    )

    # make axis names collide
    axes = [
        Axis(name="x", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]

    with pytest.raises(ValidationError, match="Axis names must be unique."):
        Multiscale(
            name="a",
            axes=axes,
            datasets=[datasets],
            coordinateTransformations=[scale],
        )


@pytest.mark.parametrize(
    "axis_types",
    (
        ("space", "space", "channel"),
        ("space", "channel", "space", "channel"),
        (None, "space", "space", None),
        ("time", "time"),
    ),
)
def test_multiscale_semantic_axis_order(axis_types: List[Optional[str]]):
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
                VectorScaleTransform(
                    scale=[
                        1,
                    ]
                    * rank
                ),
                VectorTranslationTransform(
                    translation=[
                        0,
                    ]
                    * rank
                ),
            ],
        )
    ]
    # TODO: make some axis-specifc exceptions
    with pytest.raises(ValidationError):
        Multiscale(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=[
                VectorScaleTransform(
                    scale=[
                        1,
                    ]
                    * rank
                ),
            ],
        )


@pytest.mark.parametrize("num_axes", (0, 1, 6, 7))
def test_multiscale_axis_length(num_axes: int):
    rank = num_axes
    axes = [Axis(name=str(idx), type="space", unit="meter") for idx in range(num_axes)]
    datasets = [
        MultiscaleDataset(
            path="path",
            coordinateTransformations=[
                VectorScaleTransform(
                    scale=[
                        1,
                    ]
                    * rank
                ),
                VectorTranslationTransform(
                    translation=[
                        0,
                    ]
                    * rank
                ),
            ],
        )
    ]
    with pytest.raises(ValidationError, match="Too many axes"):
        Multiscale(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=[
                VectorScaleTransform(
                    scale=[
                        1,
                    ]
                    * rank
                ),
            ],
        )


@pytest.mark.parametrize(
    "tforms",
    (
        [
            VectorScaleTransform(scale=(1, 1, 1)),
            VectorTranslationTransform(translation=(1, 1, 1)),
            VectorTranslationTransform(translation=(1, 1, 1)),
        ],
        [
            VectorScaleTransform(scale=(1, 1, 1)),
        ]
        * 4,
    ),
)
def test_coordinate_transforms_invalid_length(
    tforms: Tuple[CoordinateTransform, CoordinateTransform]
):
    with pytest.raises(ValueError, match="Too many coordinateTransformations"):
        Transforms.validate(tforms)


@pytest.mark.parametrize(
    "tforms",
    (
        [
            VectorTranslationTransform(translation=(1, 1, 1)),
        ],
        [VectorScaleTransform(scale=(1, 1, 1)), VectorScaleTransform(scale=(1, 1, 1))],
        [
            VectorTranslationTransform(translation=(1, 1, 1)),
            VectorScaleTransform(scale=(1, 1, 1)),
        ],
    ),
)
def test_coordinate_transforms_invalid_elements(
    tforms: Tuple[CoordinateTransform, CoordinateTransform]
):
    with pytest.raises(ValueError, match="element of coordinateTransformations must"):
        Transforms.validate(tforms)


@pytest.mark.parametrize("dim_scale,dim_trans", ((2, 3), (4, 3)))
def test_transforms_ndim(dim_scale, dim_trans):
    scale = VectorScaleTransform(
        scale=[
            1,
        ]
        * dim_scale
    )
    trans = VectorTranslationTransform(
        translation=[
            0,
        ]
        * dim_trans
    )
    with pytest.raises(ValueError, match="must have the same dimensionality"):
        Transforms.validate([scale, trans])


def test_multiscale_group_datasets_exist(default_multiscale: Multiscale):
    with pytest.raises(
        ValidationError,
        match="array with that name was found in the children of that group.",
    ):
        bad_children = [
            Array(name=d.path + "bla", shape=(1, 1, 1, 1), dtype="")
            for d in default_multiscale.datasets
        ]
        MultiscaleGroup(
            name="",
            attrs={"multiscales": [default_multiscale.dict()]},
            children=bad_children,
        )


def test_multiscale_group_datasets_consistent_ndim(default_multiscale: Multiscale):
    with pytest.raises(
        ValidationError, match="All arrays must have the same dimensionality."
    ):
        # arrays with varying dimensionality
        bad_children = [
            Array(name=d.path, shape=(1,) * (idx + 1), dtype="")
            for idx, d in enumerate(default_multiscale.datasets)
        ]
        MultiscaleGroup(
            name="",
            attrs={"multiscales": [default_multiscale.dict()]},
            children=bad_children,
        )


def test_multiscale_group_datasets_transform_ndim(default_multiscale: Multiscale):
    with pytest.raises(ValidationError, match="Transform dimensionality"):
        # arrays with rank that doesn't match the transform
        bad_children = [
            Array(name=d.path, shape=(1,), dtype="")
            for d in default_multiscale.datasets
        ]
        MultiscaleGroup(
            name="",
            attrs={"multiscales": [default_multiscale.dict()]},
            children=bad_children,
        )
