from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Literal

from pydantic import BeforeValidator

from pydantic_ome_ngff.base import FrozenBase
from pydantic_ome_ngff.utils import ArrayLike, listify_numpy


class Identity(FrozenBase):
    """
    An identity transform. It has no parameters other than `type`, and no valid use according to the spec.

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------

    type: Literal["identity"]
        The string "identity".

    """

    type: Literal["identity"] = "identity"

    @property
    def ndim(self) -> int:
        raise NotImplementedError


class PathTranslation(FrozenBase):
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

    @property
    def ndim(self) -> int:
        raise NotImplementedError


class PathScale(FrozenBase):
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

    @property
    def ndim(self) -> int:
        raise NotImplementedError


class VectorTranslation(FrozenBase):
    """
    A translation transformation defined by a sequence of numbers.

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------
    type: Literal["translation"]
        The string "translation".
    translation: tuple[float | int]
        A sequence of numbers that define an N-dimensional translation transformation.
    """

    type: Literal["translation"] = "translation"
    translation: Annotated[tuple[float | int, ...], BeforeValidator(listify_numpy)]

    @property
    def ndim(self) -> int:
        return ndim(self)


class VectorScale(FrozenBase):
    """
    A scaling transformation defined by a sequence of numbers.

    See [https://ngff.openmicroscopy.org/0.4/#trafo-md](https://ngff.openmicroscopy.org/0.4/#trafo-md) for the specification of this data structure.

    Attributes
    ----------
    type: Literal["scale"]
        The string "scale".
    scale: tuple[float | int]
        A sequence of numbers that define an  N-dimensional scaling transformation.
    """

    type: Literal["scale"] = "scale"
    scale: Annotated[tuple[float | int, ...], BeforeValidator(listify_numpy)]

    @property
    def ndim(self) -> int:
        return ndim(self)


def ndim(
    transform: Scale | Translation,
) -> int:
    """
    Get the dimensionality of a scale or translation transform.
    """
    if hasattr(transform, "scale"):
        return len(transform.scale)
    elif hasattr(transform, "translation"):
        return len(transform.translation)
    else:
        msg = f"Cannot infer the dimensionality of {type(transform)}"
        raise TypeError(msg)


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

    vec_scale = VectorScale(scale=tuple(scale))

    if len(translation) != len_scale:
        msg = (
            f"Length of `scale` and `translation` do not match. `scale` has length = {len_scale}"
            f"but `translation` has length = {len_translation}"
        )
        raise ValueError(msg)

    vec_trans = VectorTranslation(translation=tuple(translation))

    return (vec_scale, vec_trans)


Scale = VectorScale | PathScale
Translation = VectorTranslation | PathTranslation
Transform = Scale | Translation


def ensure_dimensionality(
    transforms: Sequence[Scale | Translation],
) -> Sequence[Scale | Translation]:
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
    array: ArrayLike, transforms: Sequence[VectorScale | VectorTranslation]
) -> bool:
    """
    Check if an array is consistent, in terms of dimensionality, with a collection of transforms.
    """
    # check that the transforms are themselves consistent
    transforms_checked = ensure_dimensionality(transforms=transforms)
    # we only need to compare the array to the first transform
    return len(array.shape) == ndim(transforms_checked[0])
