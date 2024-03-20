from __future__ import annotations
from typing import Sequence, Tuple
import pytest
from pydantic_ome_ngff.v04.transform import (
    VectorScale,
    VectorTranslation,
    ensure_dimensionality,
    ndim,
    scale_translation,
)


@pytest.mark.parametrize(
    "scale, translation",
    (
        [(0,), (0,)],
        [(1, 1), (0, 0)],
        [(1,), (0, 0)],
        [(), (10,)],
        [(10,), ()],
    ),
)
def test_scale_translation(
    scale: Tuple[int, ...], translation: Tuple[int, ...]
) -> None:
    if len(scale) == len(translation):
        result = scale_translation(scale=scale, translation=translation)
        assert isinstance(result[0], VectorScale)
        assert isinstance(result[1], VectorTranslation)
        assert result[0].scale == scale
        assert result[1].translation == translation
    else:
        if len(scale) == 0:
            match = "Not enough values in scale. Got 0, expected at least 1."
        elif len(translation) == 0:
            match = "Not enough values in translation. Got 0, expected at least 1."
        else:
            match = (
                f"Length of `scale` and `translation` do not match. `scale` has length = {len(scale)}"
                f"but `translation` has length = {len(translation)}"
            )
        with pytest.raises(ValueError, match=match):
            scale_translation(scale, translation)


@pytest.mark.parametrize(
    "data",
    [
        (VectorScale(scale=(10, 10)), VectorTranslation(translation=(1,))),
        (VectorScale(scale=(10,)), VectorTranslation(translation=(1, 1))),
    ],
)
def test_ensure_dimensionality(data: Sequence[VectorScale | VectorTranslation]) -> None:
    with pytest.raises(
        ValueError, match="The transforms have inconsistent dimensionality."
    ):
        ensure_dimensionality(data)


def test_ndim() -> None:
    tx = VectorScale(scale=(1, 1, 1))
    assert ndim(tx) == 3

    tx = VectorTranslation(translation=(1, 1, 1))
    assert ndim(tx) == 3
