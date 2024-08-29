from __future__ import annotations

from typing import Literal

import pydantic_ome_ngff.v04.multiscale as msv04
from pydantic_ome_ngff.latest.base import version


class Dataset(msv04.Dataset):
    """
    A single entry in the multiscales.datasets list.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md

    Note that this class is unchanged from the v04 counterpart.

    Attributes:
    ----------
    path: str
        The path to the Zarr array that stores the image described by this metadata.
        This path should be relative to the group that contains this metadata.
    coordinateTransformations: ctx.ScaleTransform | ctx.TranslationTransform
        The coordinate transformations for this image.
    """


class MultiscaleMetadata(msv04.MultiscaleMetadata):
    """
    Multiscale image metadata.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md
    """

    _version = version
    version: Literal["0.5-dev"] = version


class GroupAttrs(msv04.MultiscaleGroupAttrs):
    """
    Attributes of a multiscale group.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md
    """


class Group(msv04.MultiscaleGroup):
    """
    A model of a Zarr group that implements OME-NGFF Multiscales metadata, version 0.5-dev.

    Attributes
    ----------

    attributes: MultiscaleAttrs
        The attributes of this Zarr group, which should contain valid `MultiscaleAttrs`. Extra
        values are allowed.
    members Dict[Str, ArraySpec | GroupSpec]:
        The members of this Zarr group. Should be instances of `pydantic_zarr.GroupSpec` or `pydantic_zarr.ArraySpec`.

    """
