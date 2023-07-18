from __future__ import annotations
from pydantic_ome_ngff.base import StrictVersionedBase
from pydantic_ome_ngff.v04.base import version
import warnings
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import validator
import textwrap


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


class Axis(StrictVersionedBase):
    """
    Axis metadata.
    See https://ngff.openmicroscopy.org/0.4/#axes-md
    """

    _version = version
    # SPEC: this should almost certainly be a string, but the spec doesn't specify the type: https://github.com/ome/ngff/blob/ee4d5dab677636a28f1f65c248a751e279a0d1fe/0.4/index.bs#L243
    name: Any
    type: Optional[str]
    unit: Optional[str]

    @validator("unit")
    def check_unit(cls, unit: str, values: Dict[str, AxisType]) -> str:
        typ = values["type"]
        if typ == AxisType.space:
            if unit not in SpaceUnit.__members__:
                msg = (
                    f'Unit "{unit}" is not recognized as a standard unit for an '
                    f'axis with type "{typ}".'
                )
                warnings.warn(textwrap.fill(msg))

        elif typ == AxisType.time:
            if unit not in TimeUnit.__members__:
                msg = (
                    f'Unit "{unit}" is not recognized as a standard unit for an '
                    f'axis with type "{typ}".'
                )
                warnings.warn(textwrap.fill(msg))
        elif typ == AxisType.channel:
            pass
        elif typ is None:
            msg = (
                f"Null axis type. Version {cls._version} of the OME-NGFF spec "
                "states that the `type` field of an axis should be a string."
            )
            warnings.warn(textwrap.fill(msg))
        else:
            msg = (
                f'Unknown axis type "{typ}". Version {cls._version} of the '
                "OME-NGFF spec states that the `type` field of an axis should be "
                f"one of {AxisType._member_names_}."
            )
            warnings.warn(textwrap.fill(msg))
        if unit is None:
            msg = (
                f"Null unit. Version {cls._version} of the OME-NGFF spec states "
                "that the `unit` field of an axis should be a string."
            )
            warnings.warn(textwrap.fill(msg))
        return unit
