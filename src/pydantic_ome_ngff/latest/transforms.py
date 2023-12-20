from typing import Union
import pydantic_ome_ngff.v04.transforms as ctx


class IdentityTransform(ctx.Identity):
    """
    An identity transform with no parameters.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class PathScale(ctx.PathScale):
    """ "
    A coordinateTransform with at "path" field.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class PathTranslation(ctx.PathTranslation):
    """ "
    A coordinateTransform with at "path" field.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class VectorTranslationTransform(ctx.VectorTranslation):
    """
    A translation transform with a `translate` field that is a vector.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class VectorScaleTransform(ctx.VectorScale):
    """
    A scale transform with a `scale` field that is a vector.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


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
        raise ValueError(
            f"""
        Transform must be either VectorScaleTransform or VectorTranslationTransform.
        Got {type(transform)} instead.
        """
        )


ScaleTransform = Union[VectorScaleTransform, PathScale]
TranslationTransform = Union[VectorTranslationTransform, PathTranslation]
CoordinateTransform = Union[ScaleTransform, TranslationTransform, IdentityTransform]
