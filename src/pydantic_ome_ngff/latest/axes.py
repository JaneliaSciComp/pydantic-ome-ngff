import warnings
from pydantic import validator
from pydantic_ome_ngff.base import StrictVersionedBase
from pydantic_ome_ngff.latest import version
from typing import Any, Optional
from pydantic_ome_ngff.v04.axes import AxisType, SpaceUnit, TimeUnit


class Axis(StrictVersionedBase):
    """
    Axis metadata.
    See https://ngff.openmicroscopy.org/latest/#axes-md
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
