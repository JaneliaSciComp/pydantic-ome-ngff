import requests
from typing import Any, Tuple
import jsonschema as jsc

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
        Axis(name="x", type="space", units="meter"),
        Axis(name="y", type="space", units="meter"),
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

    multi = Multiscale(
        name="foo",
        axes=axes,
        type="foo",
        datasets=datasets,
        coordinateTransformations=[
            VectorScaleTransform(scale=[1, 1, 1]),
            VectorTranslationTransform(translation=[0, 0, 0]),
        ],
    )
    sample = {"multiscales": [multi.dict()]}

    jsc.validate(sample, strict_schema)
