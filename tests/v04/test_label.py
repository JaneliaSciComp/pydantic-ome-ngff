from __future__ import annotations
from typing import List, Literal
import pytest
from pydantic import ValidationError
from pydantic_ome_ngff.v04 import version as NGFF_VERSION

from pydantic_ome_ngff.v04.label import Color, ImageLabel, Property


@pytest.mark.parametrize("version", (None, "0.4"))
def test_imagelabel(version: Literal["0.4"] | None):
    color = Color(label_value=1, rgba=[0, 0, 0, 0])
    model = ImageLabel(colors=[color], version=version)
    dumped = model.model_dump()

    assert dumped["colors"] == [color.model_dump()]
    # check that if the version is None, then we didn't write it out
    if version == "0.4":
        assert dumped["version"] == NGFF_VERSION


def test_properties_colors_match():
    color = Color(label_value=0, rgba=(0, 0, 0, 0))
    prop = Property(label_value=1)

    with pytest.raises(
        ValidationError,
        match="Inconsistent `label_value` attributes in `colors` and `properties`.",
    ):
        ImageLabel(colors=[color], properties=[prop])


@pytest.mark.parametrize("version", ("0.5", "0.3"))
def test_imagelabel_version(version: str) -> None:
    with pytest.raises(ValidationError, match="Input should be '0.4'"):
        _ = ImageLabel(version=version)


@pytest.mark.parametrize(
    "colors",
    (
        None,
        [
            Color(label_value=10, rgba=[0, 0, 0, 0]),
            Color(label_value=10, rgba=[0, 0, 0, 0]),
        ],
    ),
)
def test_imagelabel_colors(colors: List[Color] | None):
    if colors is None:
        with pytest.warns(UserWarning):
            ImageLabel(colors=colors)
    else:
        with pytest.raises(ValidationError, match="Duplicated label-value"):
            ImageLabel(colors=colors)
