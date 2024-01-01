from typing import List
import pytest
from pydantic import ValidationError


from pydantic_ome_ngff.v04.label import Color, ImageLabel

@pytest.mark.parametrize('version', ('0.4', None))
def test_imagelabel_version(version: str | None) -> None:
    if version is None:
        with pytest.warns(UserWarning):
            model = ImageLabel(version=version)
    else:
        model = ImageLabel(version=version)
    assert model.version == version

@pytest.mark.parametrize('colors', (None, 
                                    [Color(label_value=10, rgba=[0,0,0,0]), Color(label_value=10, rgba=[0,0,0,0])]))
def test_imagelabel_colors(colors: List[Color] | None):
    if colors is None:
        with pytest.warns(UserWarning):
            model = ImageLabel(colors=colors)
    else:
        with pytest.raises(ValidationError, match='Duplicated label-value'):
            model=ImageLabel(colors=colors)