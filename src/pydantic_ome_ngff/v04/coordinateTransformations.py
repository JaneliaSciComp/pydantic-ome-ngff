from typing import Any, Iterable, List, Literal, Union

from pydantic_ome_ngff.base import StrictBase


class IdentityTransform(StrictBase):
    """
    An identity transform with no parameters.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    # SPEC why does this exist, as opposed to translation by 0 or scale by 1?
    type: str = "identity"

    @property
    def ndim(self):
        msg = "Cannot get the dimensionality of an identity transform."
        raise NotImplementedError(msg)


class PathTransform(StrictBase):
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

    @property
    def ndim(self):
        msg = "Cannot get the dimensionality of a transform with a path parameter."
        raise NotImplementedError(msg)


class VectorTranslationTransform(StrictBase):
    """
    A translation transform with a `translate` field that is a vector.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["translation"] = "translation"
    translation: List[
        float
    ]  # SPEC: redundant field name -- we already know it's translation

    @property
    def ndim(self) -> int:
        return len(self.translation)


class VectorScaleTransform(StrictBase):
    """
    A scale transform with a `scale` field that is a vector.
    See https://ngff.openmicroscopy.org/0.4/#trafo-md
    """

    type: Literal["scale"] = "scale"
    scale: List[float]  # SPEC: redundant field name -- we already know it's scale

    @property
    def ndim(self) -> int:
        return len(self.scale)


ScaleTransform = Union[VectorScaleTransform, PathTransform]
TranslationTransform = Union[VectorTranslationTransform, PathTransform]
CoordinateTransform = Union[ScaleTransform, TranslationTransform, IdentityTransform]


def _transform_from_dict(transform: dict[str, Any]) -> CoordinateTransform:
    """
    Convert a CoordinateTransform from a dict into the respective pydantic model.
    There is almost certainly a better way to do this.
    """
    errs = []
    for typ in CoordinateTransform.__args__:
        try:
            return typ.parse_obj(transform)
        except ValueError as e:
            errs.append(e)
    raise ValueError(f"Could not parse {transform} as a CoordinateTransform")


def check_transform_order(
    transforms: Iterable[CoordinateTransform],
) -> list[CoordinateTransform]:
    tforms = list(transforms)
    num_tforms = len(tforms)

    # check that transforms are in the correct order.
    if num_tforms > 0 and (tform := tforms[0].type) != "scale":
        msg = (
            "The first element of coordinateTransformations must be a scale "
            f"transform. Got {tform} instead."
        )
        raise ValueError(msg)

    if num_tforms == 2:
        if (tform := transforms[1].type) != "translation":
            msg = (
                "The second element of coordinateTransformations must be a "
                f"translation transform. Got {tform} instead."
            )
            raise ValueError(msg)

    elif num_tforms > 2:
        msg = (
            f"Too many coordinateTransformations (got {num_tforms}). At most "
            "two coordinateTransformations are allowed."
        )
        raise ValueError(msg)

    return tforms


def check_transform_ndims(
    transforms: Iterable[CoordinateTransform],
) -> list[CoordinateTransform]:
    tforms = list(transforms)
    # check that dimensionality is consistent
    ndims: list[int] = []
    for tx in tforms:
        try:
            ndims.append(tx.ndim)
        except NotImplementedError:
            continue

    if len(set(ndims)) > 1:
        msg = (
            "Elements of coordinateTransformations must have the same "
            f"dimensionality. Got elements with dimensionality = {ndims}."
        )
        raise ValueError(msg)

    return tforms


class Transforms(list[CoordinateTransform]):
    """
    A list of coordinateTransforms that can be validated by pydantic.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        tforms = []
        for tform in v:
            if isinstance(tform, dict):
                tforms.append(_transform_from_dict(tform))
            else:
                tforms.append(tform)
        tforms = check_transform_ndims(tforms)
        tforms = check_transform_order(tforms)
        return cls(tforms)

    @property
    def ndim(self):
        if len(self) > 0:
            return self[0].ndim
        else:
            return 1
