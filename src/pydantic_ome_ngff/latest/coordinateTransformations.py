from __future__ import annotations
import pydantic_ome_ngff.v04.coordinateTransformations as ctx


class IdentityTransform(ctx.IdentityTransform):
    """
    An identity transform with no parameters.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class PathTransform(ctx.PathTransform):
    """ "
    A coordinateTransform with at "path" field.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class VectorTranslationTransform(ctx.VectorTranslationTransform):
    """
    A translation transform with a `translate` field that is a vector.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class VectorScaleTransform(ctx.VectorScaleTransform):
    """
    A scale transform with a `scale` field that is a vector.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


def get_transform_ndim(
    transform: VectorScaleTransform | VectorTranslationTransform,
) -> int:
    """
    Get the dimensionality of a vector transform (scale or translation).
    """
    if transform.type == "scale" and hasattr(transform, "scale"):
        return len(transform.scale)
    elif transform.type == "translation" and hasattr(transform, "translation"):
        return len(transform.translation)
    else:
        msg = f"""
        Transform must be either VectorScaleTransform or VectorTranslationTransform.
        Got {type(transform)} instead.
        """

        raise ValueError(msg)


ScaleTransform = VectorScaleTransform | PathTransform
TranslationTransform = VectorTranslationTransform | PathTransform
CoordinateTransform = ScaleTransform | TranslationTransform | IdentityTransform
