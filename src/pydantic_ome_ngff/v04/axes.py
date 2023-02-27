from pydantic_ome_ngff.base import StrictVersionedBase
from pydantic_ome_ngff.v04 import version
import warnings
from enum import Enum
from typing import Any, Optional
from pydantic import validator


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
    def check_unit(cls, unit, values):
        type = values["type"]
        if type == AxisType.space:
            if unit not in SpaceUnit.__members__:
                warnings.warn(
                    f"""
                Unit "{unit}" is not recognized as a standard unit for an axis with 
                type "{type}".
                """,
                    UserWarning,
                )
        elif type == AxisType.time:
            if unit not in TimeUnit.__members__:
                warnings.warn(
                    f"""
                Unit "{unit}" is not recognized as a standard unit for an axis with 
                type "{type}".
                """,
                    UserWarning,
                )
        elif type == AxisType.channel:
            pass
        elif type is None:
            warnings.warn(
                f"""
             Null axis type. Version {cls._version} of the OME-NGFF spec states that 
             the "type" field of an axis should be set to a string.
            """,
                UserWarning,
            )
        else:
            warnings.warn(
                f"""
            Unknown axis type "{type}". Version {cls._version} of the OME-NGFF spec 
            states that the "type" field of an axis should be one of 
            {AxisType._member_names_}.
            """,
                UserWarning,
            )

        if unit is None:
            warnings.warn(
                f"""
            Null unit. Version {cls._version} of the OME-NGFF spec states
            that the `unit` field of an axis should be set to a string.
            """,
                UserWarning,
            )
        return unit
