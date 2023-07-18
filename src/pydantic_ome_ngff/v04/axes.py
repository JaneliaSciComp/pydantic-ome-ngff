from collections import Counter
from pydantic_ome_ngff.base import StrictVersionedBase
from pydantic_ome_ngff.utils import duplicates
from pydantic_ome_ngff.v04.base import version
import warnings
from enum import Enum
from typing import Any, Dict, Optional
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
    def check_unit(cls, unit: str, values: Dict[str, AxisType]) -> str:
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


class Axes(list[Axis]):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        axes: list[Axis] = []
        for ax in v:
            if isinstance(ax, dict):
                axes.append(Axis.parse_obj(ax))
            else:
                axes.append(ax)
        num_axes = len(axes)
        if num_axes < 2 or num_axes > 5:
            msg = (
                f"Too many axes. Got {num_axes} axes, "
                "but only 2 - 5 (inclusive) axes are allowed."
            )
            raise ValueError(msg)

        name_dupes = duplicates(a.name for a in axes)
        if len(name_dupes) > 0:
            msg = (
                "Axis names must be unique. "
                f"Axis names {tuple(name_dupes.keys())} are repeated."
            )
            raise ValueError(msg)
        axis_types = [ax.type for ax in axes]
        type_census = Counter(axis_types)
        num_spaces = type_census["space"]
        if num_spaces < 2 or num_spaces > 3:
            msg = (
                f"Invalid number of space axes: {num_spaces}. Only 2 or 3 space axes "
                "are allowed."
            )
            raise ValueError(msg)

        elif not all(a == "space" for a in axis_types[-num_spaces:]):
            msg = f"Space axes must come last. Got axes with order: {axis_types}"
            raise ValueError(msg)

        if (num_times := type_census["time"]) > 1:
            msg = (
                f"Invalid number of time axes: {num_times}. "
                "Only 1 time axis is allowed."
            )
            raise ValueError(msg)

        if (num_channels := type_census["channel"]) > 1:
            msg = (
                f"Invalid number of channel axes: {num_channels}. "
                "Only 1 channel axis is allowed."
            )
            raise ValueError(msg)

        custom_axes = set(axis_types) - set(AxisType._member_names_)
        if len(custom_axes) > 1:
            msg = (
                f"Invalid number of custom axes: {custom_axes}. Only 1 custom axis is"
                " allowed"
            )
            raise ValueError(msg)

        return cls(axes)
