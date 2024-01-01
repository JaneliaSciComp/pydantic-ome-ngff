from __future__ import annotations
from collections import Counter
from typing import Any, Dict, List, Literal, Optional, Union, cast
import warnings

from pydantic import BaseModel, model_validator, field_validator
from pydantic_ome_ngff.base import StrictBase, StrictVersionedBase
from pydantic_ome_ngff.latest.base import version
from pydantic_ome_ngff.latest import transforms as ctx
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.latest.axis import AxisType, Axis
import pydantic_ome_ngff.v04.multiscales as msv04
from pydantic_zarr.v2 import GroupSpec, ArraySpec


class MultiscaleDataset(msv04.MultiscaleDataset):
    """
    A single entry in the multiscales.datasets list.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md

    Note that this class is unchanged from the v04 counterpart.

    Attributes:
    ----------
    path: str
        The path to the zarr array that stores the image described by this metadata.
        This path should be relative to the group that contains this metadata.
    coordinateTransformations: ctx.ScaleTransform | ctx.TranslationTransform
        The coordinate transformations for this image.
    """
    ...

class Multiscale(msv04.Multiscale):
    """
    Multiscale image metadata.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md
    """
    _version = version
    version: Literal['0.5-dev'] = version

class MultiscaleAttrs(msv04.MultiscaleAttrs):
    """
    Attributes of a multiscale group.
    See https://ngff.openmicroscopy.org/latest/#multiscale-md
    """

class MultiscaleGroup(msv04.MultiscaleGroup):
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