from __future__ import annotations

from typing import Annotated, Literal, Sequence

from pydantic import BeforeValidator

from pydantic_ome_ngff.base import StrictBase

from pydantic_ome_ngff.utils import ArrayLike, listify_numpy


class Identity(StrictBase):
    """
    An identity transform. It has no parameters other than `type`, and no valid use according to the spec.

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------

    type: Literal["identity"]
        The string "identity".

    """

    type: Literal["identity"] = "identity"


class PathTranslation(StrictBase):
    """
    A translation transformation with a `path` field. The spec states that `path` should resolve to "binary data".

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------

    type: Literal["translation"]
        The string "translation".
    path: str
        A string reference to something that can be interpreted as defining a translation transformation.
    """

    type: Literal["translation"] = "translation"
    path: str


class PathScale(StrictBase):
    """
    A scaling transformation with a `path` field. The spec states that `path` should resolve to "binary data".

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------
    type: Literal["scale"]
        The string "scale".
    path: str
        A string reference to something that can be interpreted as defining a scaling transformation.
    """

    type: Literal["scale"] = "scale"
    path: str


class VectorTranslation(StrictBase):
    """
    A translation transformation defined by a sequence of numbers.

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------
    type: Literal["translation"]
        The string "translation".
    translation: Sequence[float | int]
        A sequence of numbers that define an N-dimensional translation transformation.
    """

    type: Literal["translation"] = "translation"
    translation: Annotated[Sequence[float | int], BeforeValidator(listify_numpy)]


class VectorScale(StrictBase):
    """
    A scaling transformation defined by a sequence of numbers.

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------
    type: Literal["scale"]
        The string "scale".
    scale: Sequence[float | int]
        A sequence of numbers that define an  N-dimensional scaling transformation.
    """

    type: Literal["scale"] = "scale"
    scale: Annotated[Sequence[float | int], BeforeValidator(listify_numpy)]


def ndim(
    transform: VectorScale | VectorTranslation,
) -> int:
    """
    Get the dimensionality of a `VectorScale` or `VectorTranslation`.
    """
    if hasattr(transform, "scale"):
        return len(transform.scale)

    else:
        return len(transform.translation)


def scale_translation(
    scale: Sequence[float], translation: Sequence[float]
) -> tuple[Scale, Translation]:
    """
    Create a `VectorScale` and a `VectorTranslation` from a scale and a translation
    parameter.
    """

    len_scale = len(scale)
    len_translation = len(translation)

    if len_scale < 1:
        msg = "Not enough values in scale. Got 0, expected at least 1."
        raise ValueError(msg)

    if len_translation < 1:
        msg = "Not enough values in translation. Got 0, expected at least 1."
        raise ValueError(msg)

    vec_scale = VectorScale(scale=scale)

    if len(translation) != len_scale:
        msg = (
            f"Length of `scale` and `translation` do not match. `scale` has length = {len_scale}"
            f"but `translation` has length = {len_translation}"
        )
        raise ValueError(msg)

    vec_trans = VectorTranslation(translation=translation)

    return (vec_scale, vec_trans)


Scale = VectorScale | PathScale
Translation = VectorTranslation | PathTranslation
Transform = Scale | Translation


def ensure_dimensionality(
    transforms: Sequence[VectorScale | VectorTranslation],
) -> Sequence[VectorScale | VectorTranslation]:
    """
    Ensures that the elements in the input sequence define transformations with identical dimensionality.
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


def array_transform_consistency(
    array: ArrayLike, transforms: Sequence[VectorScale, VectorTranslation]
) -> bool:
    """
    Check if an array is consistent, in terms of dimensionality, with a collection of transforms.
    """
    # check that the transforms are themselves consistent
    transforms_checked = ensure_dimensionality(transforms=transforms)
    # we only need to compare the array to the first transform
    return len(array.shape) == ndim(transforms_checked[0])
