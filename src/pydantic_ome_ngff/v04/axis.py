from __future__ import annotations

from typing import Literal
import warnings
from enum import Enum


from pydantic_ome_ngff.base import FrozenBase, NoneSkipBase
from pydantic_ome_ngff.v04.base import version


class AxisType(str, Enum):
    """
    String enum representing the three axis types (`space`, `time`, `channel`) defined in the specification.
    """

    space = "space"
    time = "time"
    channel = "channel"


class SpaceUnit(str, Enum):
    angstrom = "angstrom"
    attometer = "attometer"
    centimeter = "centimeter"
    decimeter = "decimeter"
    exameter = "exameter"
    femtometer = "femtometer"
    foot = "foot"
    gigameter = "gigameter"
    hectometer = "hectometer"
    inch = "inch"
    kilometer = "kilometer"
    megameter = "megameter"
    meter = "meter"
    micrometer = "micrometer"
    mile = "mile"
    millimeter = "millimeter"
    nanometer = "nanometer"
    parsec = "parsec"
    petameter = "petameter"
    picometer = "picometer"
    terameter = "terameter"
    yard = "yard"
    yoctometer = "yoctometer"
    yottameter = "yottameter"
    zeptometer = "zeptometer"
    zettameter = "zettameter"


class TimeUnit(str, Enum):
    attosecond = "attosecond"
    centisecond = "centisecond"
    day = "day"
    decisecond = "decisecond"
    exasecond = "exasecond"
    femtosecond = "femtosecond"
    gigasecond = "gigasecond"
    hectosecond = "hectosecond"
    hour = "hour"
    kilosecond = "kilosecond"
    megasecond = "megasecond"
    microsecond = "microsecond"
    millisecond = "millisecond"
    minute = "minute"
    nanosecond = "nanosecond"
    petasecond = "petasecond"
    picosecond = "picosecond"
    second = "second"
    terasecond = "terasecond"
    yoctosecond = "yoctosecond"
    yottasecond = "yottasecond"
    zeptosecond = "zeptosecond"
    zettasecond = "zettasecond"


def check_type_unit(model: Axis) -> Axis:
    """
    Check that the `unit` attribute of an `Axis` object is valid.
    This function emits warnings when the `unit` attribute of of an `Axis` object
    is spec-compliant but contravenes a "SHOULD" statement in the spec.
    """

    typ = model.type
    unit = model.unit

    if typ == AxisType.space:
        if unit not in [e.value for e in SpaceUnit]:
            msg = (
                f"Unit '{unit}' is not recognized as a standard unit "
                f"for an axis with type '{typ}'."
            )
            warnings.warn(msg, stacklevel=1)
    elif typ == AxisType.time:
        if unit not in [e.value for e in TimeUnit]:
            msg = (
                f"Unit '{unit}' is not recognized as a standard unit "
                f"for an axis with type '{typ}'."
            )
            warnings.warn(msg, stacklevel=1)
    elif typ == AxisType.channel:
        pass
    elif typ is None:
        msg = (
            f"The `type` field of this axis was set to `None`. Version {model._version} of the OME-NGFF spec states "
            "that the 'type' field of an axis should be set to a string."
        )
        warnings.warn(msg, stacklevel=1)
    else:
        msg = (
            f"Unknown axis type '{typ}'. Version {model._version} of the OME-NGFF "
            " spec states that the 'type' field of an axis should be one of "
            f"{AxisType._member_names_}."
        )
        warnings.warn(msg, stacklevel=1)

    if unit is None:
        msg = (
            f"The `unit` field of this axis was set to `None`. Version {model._version} of the OME-NGFF spec states "
            "that the `unit` field of an axis should be set to a string."
        )
        warnings.warn(msg, stacklevel=1)
    return model


class Axis(NoneSkipBase, FrozenBase):
    """
    Axis metadata.

    See [https://ngff.openmicroscopy.org/0.4/#axes-md](https://ngff.openmicroscopy.org/0.4/#axes-md) for the specification of this data structure.

    Attributes
    ----------
    _version: Literal['0.4']
        The current version of this metadata.
    _skip_if_none: tuple[str,...], default=("type", "unit")
        Names of fields that will not be serialized if they are None.
    name: str
        The name for this axis.
    type: str | None = None
        The type for this axis, e.g. "space".
        If this is set to None, it will not be serialized.
    unit: str | None
        The unit of measure associated with the interval defined by this axis.
        If this is set to None, it will not be serialized.
    """

    _version = version
    _skip_if_none: tuple[Literal["type"], Literal["unit"]] = "type", "unit"
    name: str
    type: str | None = None
    unit: str | None = None
