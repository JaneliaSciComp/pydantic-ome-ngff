import warnings
from pydantic import model_validator
from pydantic_ome_ngff.base import StrictVersionedBase
from pydantic_ome_ngff.latest.base import version
from typing import Any, Optional
from pydantic_ome_ngff.v04.axes import AxisType, SpaceUnit, TimeUnit


class Axis(axv04.Axis):
    """
    Axis metadata.
    See https://ngff.openmicroscopy.org/latest/#axes-md
    """

    _version = version
    # SPEC: this should almost certainly be a string, but the spec doesn't specify the type: https://github.com/ome/ngff/blob/ee4d5dab677636a28f1f65c248a751e279a0d1fe/0.4/index.bs#L243
    name: Any
    type: Optional[str]
    unit: Optional[str]

    @model_validator(mode="after")
    def check_units(self) -> "Axis":
        typ = self.type
        unit = self.unit
        if typ == AxisType.space:
            if unit not in SpaceUnit.__members__:
                msg = (
                    f"Unit '{unit}' is not recognized as a standard unit for "
                    f" an axis with type '{typ}''."
                )
                warnings.warn(msg)
        elif typ == AxisType.time:
            if unit not in TimeUnit.__members__:
                msg = (
                    f"Unit '{unit}' is not recognized as a standard unit for an axis "
                    f"with type '{typ}'."
                )
                warnings.warn(msg)
        elif typ == AxisType.channel:
            pass
        elif typ is None:
            msg = (
                f"Null axis type. Version {self._version} of the OME-NGFF spec states "
                "that the 'type' field of an axis should be set to a string."
            )
            warnings.warn(msg, UserWarning)
        else:
            msg = (
                f"Unknown axis type '{typ}'. Version {self._version} of the OME-NGFF "
                " spec states that the 'type' field of an axis should be one of "
                f"{AxisType._member_names_}."
            )
            warnings.warn(msg)

        if unit is None:
            msg = (
                f"Null unit. Version {self._version} of the OME-NGFF spec states "
                "that the `unit` field of an axis should be set to a string."
            )
            warnings.warn(msg)
        return self
