from __future__ import annotations

import pydantic_ome_ngff.v04.transform as tx


class Identity(tx.Identity):
    """
    An identity transform with no parameters.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class PathScale(tx.PathScale):
    """ "
    A coordinateTransform with at "path" field.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class PathTranslation(tx.PathTranslation):
    """ "
    A coordinateTransform with at "path" field.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class VectorTranslation(tx.VectorTranslation):
    """
    A translation transform with a `translate` field that is a vector.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


class VectorScale(tx.VectorScale):
    """
    A scale transform with a `scale` field that is a vector.
    See https://ngff.openmicroscopy.org/latest/#trafo-md
    """


Scale = VectorScale | PathScale
Translation = VectorTranslation | PathTranslation
Transform = Scale | Translation | Identity

scale_translation = tx.scale_translation
ensure_dimensionality = tx.ensure_dimensionality
ndim = tx.ndim
