from __future__ import annotations
from typing import Dict, Tuple
from pydantic import ValidationError
import pytest
import jsonschema as jsc
from pydantic_zarr.v2 import ArraySpec
from pydantic_ome_ngff.v04.multiscales import (
    MultiscaleMetadata,
    GroupAttrs,
    Dataset,
    Group,
)

from pydantic_ome_ngff.v04.transforms import (
    Transform,
    VectorScale,
    VectorTranslation,
)
from pydantic_ome_ngff.v04.axis import Axis
from tests.conftest import JsonLoader, fetch_schemas
import numpy as np
from itertools import accumulate
import operator

loader = JsonLoader("v04")


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


def test_multiscale(multi_meta: MultiscaleMetadata) -> None:
    base_schema, strict_schema = fetch_schemas("0.4", schema_name="image")
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
                VectorScale(scale=[1, 1, 1]),
                VectorTranslation(translation=[0, 0, 0]),
            ),
        )
    ]

    with pytest.raises(ValidationError, match="Axis names must be unique."):
        MultiscaleMetadata(
            name="foo",
            axes=axes,
            datasets=datasets,
            coordinateTransformations=(VectorScale(scale=[1, 1, 1]),),
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
            ax = Axis(name=str(idx), type=t, unit=units_map.get(t, None))
        else:
            ax = Axis(name=str(idx), type=t, unit=units_map.get(t, None))
        axes.append(ax)

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
    multi_meta: MultiscaleMetadata,
) -> None:
    meta_ndim = len(multi_meta.axes)
    group_attrs = GroupAttrs(multiscales=[multi_meta])
    good_members = {
        d.path: ArraySpec(
            shape=(1,) * meta_ndim,
            dtype="uint8",
            chunks=(1,) * meta_ndim,
        )
        for d in multi_meta.datasets
    }
    Group(attributes=group_attrs, members=good_members)

    with pytest.raises(
        ValidationError,
        match="array with that name was found in the hierarchy",
    ):
        Group(attributes=group_attrs, members=dict(tuple(good_members.items())[1:]))


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

    # arrays with varying rank
    bad_items = {
        d.path: ArraySpec(
            shape=(1,) * (idx + 1),
            dtype="uint8",
            chunks=(1,) * (idx + 1),
            attributes={},
        )
        for idx, d in enumerate(multi_meta.datasets)
    }

    with pytest.raises(
        ValidationError, match="All arrays must have the same dimensionality."
    ):
        Group(attributes=group_attrs, members=bad_items)

    # arrays with rank that doesn't match the transform
    bad_items = {
        d.path: ArraySpec(shape=(1,), dtype="uint8", chunks=(1,), attributes={})
        for d in multi_meta.datasets
    }
    with pytest.raises(ValidationError, match="Transform dimensionality"):
        Group(attributes=group_attrs, members=bad_items)


@pytest.mark.parametrize("name", [None, "foo"])
@pytest.mark.parametrize("type", [None, "foo"])
@pytest.mark.parametrize("path_pattern", ["{0}", "s{0}", "foo/{0}"])
@pytest.mark.parametrize("metadata", [None, {"foo": 10}])
@pytest.mark.parametrize("ndim", [2, 3, 4, 5])
def test_from_arrays(
    name: str | None,
    type: str | None,
    path_pattern: str,
    metadata: Dict[str, int] | None,
    ndim: int,
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

    group_scale = (1,) * ndim
    group_translation = (0,) * ndim

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

    group = Group.from_arrays(
        paths=paths,
        axes=axes,
        arrays=arrays,
        scales=scales,
        translations=translations,
        name=name,
        type=type,
        metadata=metadata,
        group_scale=group_scale,
        group_translation=group_translation,
    )

    group_flat = group.to_flat()

    assert group.attributes.multiscales[0].name == name
    assert group.attributes.multiscales[0].type == type
    assert group.attributes.multiscales[0].metadata == metadata
    assert group.attributes.multiscales[0].coordinateTransformations == (
        VectorScale(scale=group_scale),
        VectorTranslation(translation=group_translation),
    )
    assert group.attributes.multiscales[0].axes == axes
    for idx, array in enumerate(arrays):
        assert array.shape == group_flat["/" + paths[idx]].shape
        assert array.dtype == group_flat["/" + paths[idx]].dtype
        assert group.attributes.multiscales[0].datasets[
            idx
        ].coordinateTransformations == (
            VectorScale(scale=scales[idx]),
            VectorTranslation(translation=translations[idx]),
        )
