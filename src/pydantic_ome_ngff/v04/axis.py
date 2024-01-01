from __future__ import annotations

from pydantic import model_validator

from pydantic_ome_ngff.base import StrictVersionedBase
from pydantic_ome_ngff.v04.base import version
import warnings
from enum import Enum


class AxisType(str, Enum):
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


def check_type_unit(model: Axis) -> "Axis":
    """
    Check that the `unit` attribute of an `Axis` object is valid. This function emits warnings when the units of an `Axis` object
    are spec-compliant but go against a "SHOULD" statement in the spec.
    """

    typ = model.type
    unit = model.unit

    if typ == AxisType.space:
        if unit not in [e.value for e in SpaceUnit]:
            msg = (
                f"Unit '{unit}' is not recognized as a standard unit "
                f"for an axis with type '{typ}'."
            )
            warnings.warn(msg)
    elif typ == AxisType.time:
        if unit not in [e.value for e in TimeUnit]:
            msg = (
                f"Unit '{unit}' is not recognized as a standard unit "
                f"for an axis with type '{typ}'."
            )
            warnings.warn(msg)
    elif typ == AxisType.channel:
        pass
    elif typ is None:
        msg = (
            f"The `type` field of this axis was set to `None`. Version {model._version} of the OME-NGFF spec states "
            "that the 'type' field of an axis should be set to a string."
        )
        warnings.warn(msg, UserWarning)
    else:
        msg = (
            f"Unknown axis type '{typ}'. Version {model._version} of the OME-NGFF "
            " spec states that the 'type' field of an axis should be one of "
            f"{AxisType._member_names_}."
        )
        warnings.warn(msg)

    if unit is None:
        msg = (
            f"The `unit` field of this axis was set to `None`. Version {model._version} of the OME-NGFF spec states "
            "that the `unit` field of an axis should be set to a string."
        )
        warnings.warn(msg)
    return model


class Axis(StrictVersionedBase):
    """
    Axis metadata.
    See https://ngff.openmicroscopy.org/0.4/#axes-md
    """

    _version = version
    # SPEC: this should almost certainly be a string, but the spec doesn't specify the type: https://github.com/ome/ngff/blob/ee4d5dab677636a28f1f65c248a751e279a0d1fe/0.4/index.bs#L243
    name: str
    type: str | None
    unit: str | None

    @model_validator(mode="after")
    def check_type_unit(self):
        return check_type_unit(self)
