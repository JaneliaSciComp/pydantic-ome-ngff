from pydantic_ome_ngff.base import StrictBaseModel
from typing import Literal, Union, List

class PathTransform(
    StrictBaseModel
):  # SPEC: the existence of this type is a massive sinkhole in the spec
    # translate and scale are both so simple that nobody should be using a path
    # argument to refer to some remote resource representing a translation or a scale transform
    type: Union[Literal["scale"], Literal["translation"]]
    path: str


class VectorTranslationTransform(StrictBaseModel):
    type: Literal["translation"] = "translation"
    translation: List[float]  # SPEC: redundant field name -- we already know it's translation


class VectorScaleTransform(StrictBaseModel):
    type: Literal["scale"] = "scale"
    scale: List[float]  # SPEC: redundant field name -- we already know it's scale


ScaleTransform = Union[VectorScaleTransform, PathTransform]
TranslationTransform = Union[VectorTranslationTransform, PathTransform]
CoordinateTransform = List[Union[ScaleTransform, TranslationTransform]]