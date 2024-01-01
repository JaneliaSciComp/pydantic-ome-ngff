from __future__ import annotations

from typing import Literal, Sequence, Tuple, Union
from pydantic_ome_ngff.base import StrictBase


class Identity(StrictBase):
    """
    An identity transform. It has no parameters, and no valid use according to the spec.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: str = "identity"


class PathTranslation(StrictBase):
    """
    A coordinateTransform with a `path` field.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["translation"] = "translation"
    path: str


class PathScale(StrictBase):
    """
    A coordinateTransform with a `path` field.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["scale"] = "scale"
    path: str


class VectorTranslation(StrictBase):
    """
    A translation transform with a `translate` field that is a vector.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["translation"] = "translation"
    translation: Sequence[float | int]


class VectorScale(StrictBase):
    """
    A scale transform with a `scale` field that is a vector.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["scale"] = "scale"
    scale: Sequence[float | int]


def ndim(
    transform: Union[VectorScale, VectorTranslation],
) -> int:
    """
    Get the dimensionality of a vector transform (scale or translation).
    """
    if hasattr(transform, "scale"):
        return len(transform.scale)

    if hasattr(transform, "translation"):
        return len(transform.translation)

    msg = (
        "Transform must be either `VectorScaleTransform` or `VectorTranslationTransform`."
        f"Got {type(transform)} instead."
    )
    raise ValueError(msg)


def scale_translation(
    scale: Sequence[float], translation: Sequence[float]
) -> Tuple[Scale, Translation]:
    """
    Create a scale and transformation transformation from a scale and a translation parameter
    """
    len_scale = len(scale)
    len_translation = len(translation)
    if len_scale < 1:
        msg = f"Not enough values in scale. Got {len_scale}"
        raise ValueError(msg)
    if len_translation < 1:
        msg = f"Not enough values in `tranlsation`. Got {len_translation}"
        raise ValueError(msg)
    if len_translation != len_scale:
        msg = (
            f"Length of `scale` and `translation` do not match. `scale` has length = {len_scale}"
            f"but `translation` has length = {len_translation}"
        )
        raise ValueError(msg)

    return (VectorScale(scale=scale), VectorTranslation(translation=translation))


Scale = VectorScale | PathScale
Translation = VectorTranslation | PathTranslation
Transform = Scale | Translation


def ensure_dimensionality(
    transforms: Sequence[VectorScale | VectorTranslation],
) -> Sequence[VectorScale | VectorTranslation]:
    """
    Ensure that the elements of `Sequence[VectorTransform]`
    """
    ndims = tuple(ndim(tx) for tx in transforms)
    ndims_set = set(ndims)
    if len(ndims_set) > 1:
        msg = (
            "The transforms have inconsistent dimensionality. "
            f"Got transforms with dimensionality = {ndims}."
        )
        raise ValueError(msg)
    return transforms
