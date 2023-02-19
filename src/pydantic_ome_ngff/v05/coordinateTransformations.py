from typing import List, Literal, Union

from pydantic_ome_ngff.base import StrictBaseModel


class IdentityTransform(StrictBaseModel):
    # SPEC why does this exist, as opposed to translation by 0 or scale by 1?
    type: str = "identity"


class PathTransform(
    StrictBaseModel
):  # SPEC: the existence of this type is a massive sinkhole in the spec
    # translate and scale are both so simple that nobody should be using a path
    # argument to refer to some remote resource representing a translation
    # or a scale transform
    type: Union[Literal["scale"], Literal["translation"]]
    path: str


class VectorTranslationTransform(StrictBaseModel):
    type: Literal["translation"] = "translation"
    translation: List[
        float
    ]  # SPEC: redundant field name -- we already know it's translation


class VectorScaleTransform(StrictBaseModel):
    type: Literal["scale"] = "scale"
    scale: List[float]  # SPEC: redundant field name -- we already know it's scale


def get_transform_rank(
    transform: Union[VectorScaleTransform, VectorTranslationTransform]
) -> int:
    if transform.type == "scale":
        return len(transform.scale)
    elif transform.type == "translation":
        return len(transform.translation)
    else:
        raise ValueError(
            f"""
        Transform must be either VectorScaleTransform or VectorTranslationTransform.
        Got {type(transform)} instead.
        """
        )


ScaleTransform = Union[VectorScaleTransform, PathTransform]
TranslationTransform = Union[VectorTranslationTransform, PathTransform]
CoordinateTransform = Union[ScaleTransform, TranslationTransform, IdentityTransform]
