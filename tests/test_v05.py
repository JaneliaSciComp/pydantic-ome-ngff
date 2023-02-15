import requests
from typing import Any, Tuple, List, Optional
import jsonschema as jsc
import pytest
from pydantic import ValidationError
from pydantic_ome_ngff.v05.multiscales import Multiscale, MultiscaleDataset
from pydantic_ome_ngff.v05.coordinateTransformations import (
    VectorScaleTransform,
    VectorTranslationTransform,
)
from pydantic_ome_ngff.v05.axes import Axis


def fetch_schemas(version: str, schema_name: str) -> Tuple[Any, Any]:
    base_schema = requests.get(
        f"https://ngff.openmicroscopy.org/{version}/schemas/strict_{schema_name}.schema"
    ).json()
    strict_schema = requests.get(
        f"https://ngff.openmicroscopy.org/{version}/schemas/{schema_name}.schema"
    ).json()
    return base_schema, strict_schema


def test_multiscale():
    base_schema, strict_schema = fetch_schemas("latest", schema_name="image")
    axes = [
        Axis(name="z", type="space", units="meter"),
        Axis(name="x", type="space", units="meter"),
        Axis(name="y", type="space", units="meter"),
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
    sample = {"multiscales": [multi.dict()]}

    jsc.validate(sample, strict_schema)


def test_multiscale_unique_axis_names():
    axes = [
        Axis(name="x", type="space", units="meter"),
        Axis(name="x", type="space", units="meter"),
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
    axes = [
        Axis(name=str(idx), type=t, units=units_map.get(t, None))
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
    axes = [Axis(name=str(idx), type="space", units="meter") for idx in range(num_axes)]
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
