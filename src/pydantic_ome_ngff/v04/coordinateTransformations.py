from typing import Literal, Sequence, Union
from pydantic_ome_ngff.base import StrictBase


class IdentityTransform(BaseModel):
    """
    An identity transform with no parameters.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    # SPEC why does this exist, as opposed to translation by 0 or scale by 1?
    type: str = "identity"


class PathTransform(BaseModel):
    """
    A coordinateTransform with a `path` field.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    # SPEC: the existence of this type is a massive sinkhole in the spec
    # translate and scale are both so simple that nobody should be using a path
    # argument to refer to some remote resource representing a translation
    # or a scale transform
    type: Union[Literal["scale"], Literal["translation"]]
    path: str


class VectorTranslationTransform(BaseModel):
    """
    A translation transform with a `translate` field that is a vector.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["translation"] = "translation"
    translation: Sequence[
        Union[float, int]
    ]  # SPEC: redundant field name -- we already know it's translation


class VectorScaleTransform(BaseModel):
    """
    A scale transform with a `scale` field that is a vector.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["scale"] = "scale"
    scale: Sequence[
        Union[float, int]
    ]  # SPEC: redundant field name -- we already know it's scale


def get_transform_ndim(
    transform: Union[VectorScaleTransform, VectorTranslationTransform],
) -> int:
    """
    Get the dimensionality of a vector transform (scale or translation).
    """
    if transform.type == "scale" and hasattr(transform, "scale"):
        return len(transform.scale)
    elif transform.type == "translation" and hasattr(transform, "translation"):
        return len(transform.translation)
    else:
        msg = (
            f"Transform must be either VectorScaleTransform or "
            f"VectorTranslationTransform. Got {type(transform)} instead."
        )
        raise ValueError(textwrap.fill(msg))


ScaleTransform = Union[VectorScaleTransform, PathTransform]
TranslationTransform = Union[VectorTranslationTransform, PathTransform]
CoordinateTransform = Union[ScaleTransform, TranslationTransform, IdentityTransform]
