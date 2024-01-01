import pytest

from pydantic_ome_ngff.v04.axis import Axis

@pytest.mark.parametrize(
        'axis_type, unit', [
            ('space', 'second'), 
            ('time', 'meter'), 
            ('space', None),
            (None, None),
            ('foo', None)
            ])

def test_axis_type_unit_match_warning(axis_type: str, unit: str) -> None:
    with pytest.warns(UserWarning):
        Axis(name='axis', type=axis_type, unit=unit)

