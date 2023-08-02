from __future__ import annotations
from typing import Optional, Tuple, List, Type
import jsonschema as jsc
import pytest
from pydantic import ValidationError, BaseModel
from pydantic_ome_ngff.tree import Array
from pydantic_ome_ngff.latest.multiscales import (
    Multiscale,
    MultiscaleAttrs,
    MultiscaleDataset,
    MultiscaleGroup,
)
from pydantic_ome_ngff.latest.well import Well
from pydantic_ome_ngff.latest.plate import Plate
from pydantic_ome_ngff.latest.imageLabel import ImageLabel
from pydantic_ome_ngff.latest.coordinateTransformations import (
    CoordinateTransform,
    VectorScaleTransform,
    VectorTranslationTransform,
)
from pydantic_ome_ngff.latest.axes import Axis
from .conftest import fetch_schemas, JsonLoader

loader = JsonLoader("latest")


@pytest.fixture
def default_multiscale():
    axes = [
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


def test_multiscale(default_multiscale):
    base_schema, strict_schema = fetch_schemas("latest", schema_name="image")
    jsc.validate({"multiscales": [default_multiscale.dict()]}, strict_schema)


def test_multiscale_unique_axis_names():

    axes = [
        Axis(name="y", type="space", unit="meter"),
        Axis(name="x", type="space", unit="meter"),
    ]

    datasets = [
        MultiscaleDataset(
            path="path",
            coordinateTransformations=[
                VectorScaleTransform(scale=[1, 1, 1]),
                VectorTranslationTransform(translation=[0, 0, 0]),
            ],
        )
    ]

    Multiscale(
        name="foo",
        axes=axes,
        datasets=datasets,
        coordinateTransformations=[
            VectorScaleTransform(scale=[1, 1, 1]),
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
                VectorScaleTransform(scale=[1, 1, 1]),
                VectorTranslationTransform(translation=[0, 0, 0]),
            ],
        )
    ]

    with pytest.raises(ValidationError, match="Axis names must be unique."):
        Multiscale(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=[
                VectorScaleTransform(scale=[1, 1, 1]),
            ],
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
    axes: list[Axis] = []
    for idx, t in enumerate(axis_types):
        if t is None or t == "channel":
            with pytest.warns(UserWarning, match="Null"):
                ax = Axis(name=str(idx), type=t, unit=units_map.get(t, None))
        else:
            ax = Axis(name=str(idx), type=t, unit=units_map.get(t, None))
        axes.append(ax)

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
    with pytest.raises(ValidationError, match="type=value_error.list"):
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


def test_coordinate_transforms_invalid_ndims():
    tforms = [
        VectorScaleTransform(scale=(1, 1)),
        VectorTranslationTransform(translation=(1, 1, 1)),
    ]
    with pytest.raises(ValidationError, match="Got elements with dimensionality"):
        MultiscaleDataset(path="foo", coordinateTransformations=tforms)


@pytest.mark.parametrize(
    "transforms",
    (
        [
            VectorTranslationTransform(translation=(1, 1, 1)),
        ]
        * 3,
        [
            VectorScaleTransform(scale=(1, 1, 1)),
        ]
        * 5,
        [
            VectorScaleTransform(scale=(1, 1, 1)),
            VectorTranslationTransform(translation=(1, 1, 1)),
            VectorTranslationTransform(translation=(1, 1, 1)),
        ],
    ),
)
def test_coordinate_transforms_invalid_lenght(
    transforms: Tuple[CoordinateTransform, CoordinateTransform]
):
    with pytest.raises(ValidationError, match="ensure this value has at most 2 items"):
        MultiscaleDataset(path="foo", coordinateTransformations=transforms)


@pytest.mark.parametrize(
    "transforms",
    (
        [
            VectorTranslationTransform(translation=(1, 1, 1)),
        ]
        * 2,
        [
            VectorScaleTransform(scale=(1, 1, 1)),
        ]
        * 2,
        [
            VectorTranslationTransform(translation=(1, 1, 1)),
            VectorScaleTransform(scale=(1, 1, 1)),
        ],
    ),
)
def test_coordinate_transforms_invalid_elements(
    transforms: Tuple[CoordinateTransform, CoordinateTransform]
):
    with pytest.raises(
        ValidationError, match="element of coordinateTransformations must be a"
    ):
        MultiscaleDataset(path="foo", coordinateTransformations=transforms)


def test_multiscale_group_datasets_exist(default_multiscale: Multiscale):
    good_children = [
        Array(name=d.path, shape=(1,) * len(default_multiscale.datasets), dtype="")
        for d in default_multiscale.datasets
    ]
    MultiscaleGroup(
        name="",
        attrs={"multiscales": [default_multiscale.dict()]},
        children=good_children,
    )

    with pytest.raises(
        ValidationError,
        match="must be children of the group.",
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


def test_multiscale_group_datasets_rank(default_multiscale: Multiscale):
    good_children = [
        Array(name=d.path, shape=(1,) * len(default_multiscale.datasets), dtype="")
        for d in default_multiscale.datasets
    ]
    MultiscaleGroup(
        name="",
        attrs={"multiscales": [default_multiscale.dict()]},
        children=good_children,
    )

    with pytest.raises(
        ValidationError, match="All arrays must have the same dimensionality."
    ):
        # arrays with varying rank
        bad_children = [
            Array(name=d.path, shape=(1,) * (idx + 1), dtype="")
            for idx, d in enumerate(default_multiscale.datasets)
        ]
        MultiscaleGroup(
            name="",
            attrs={"multiscales": [default_multiscale.dict()]},
            children=bad_children,
        )

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


@pytest.mark.parametrize(
    ("fname", "key", "Class"),
    [
        ("image-label", "image-label", ImageLabel),
        ("plate0", "plate", Plate),
        ("plate1", "plate", Plate),
        ("well0", "well", Well),
        ("well1", "well", Well),
        (
            "multiscales",
            None,
            MultiscaleAttrs,
        ),
    ],
)
def test_examples(fname: str, key: str, Class: Type[BaseModel]):
    obj = loader.load_obj(fname)
    if key is not None:
        obj = obj[key]
    Class.parse_obj(obj)
