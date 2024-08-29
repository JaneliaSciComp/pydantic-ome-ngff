from __future__ import annotations

from typing import Any, Callable

import pydantic
from typing_extensions import Self


class FrozenBase(pydantic.BaseModel, frozen=True):
    """
    A frozen pydantic basemodel.
    """


class VersionedBase(pydantic.BaseModel):
    """
    An internally versioned pydantic basemodel.
    """

    _version: str = "0.0"


class SkipNoneBase(pydantic.BaseModel):
    _skip_if_none: tuple[str, ...] = ()

    @pydantic.model_serializer(mode="wrap")
    def serialize(
        self: Self,
        serializer: Callable[[SkipNoneBase], dict[str, Any]],
        info: pydantic.SerializationInfo,
    ) -> dict[str, Any]:
        return skip_none(self, serializer, info)


def skip_none(
    self: SkipNoneBase,
    serializer: Callable[[SkipNoneBase], dict[str, Any]],
    info: pydantic.SerializationInfo,
) -> dict[str, Any]:
    """
    Serialize a NoneSkipBase model to dict, skipping attributes listed in the _skip_if_none attribute of that model.
    """
    serialized = serializer(self)
    out = serialized.copy()

    for key, value in serialized.items():
        if value is None and key in self._skip_if_none:
            out.pop(key)

    if info.exclude is not None:
        for key in info.exclude:
            out.pop(key, None)

    if info.include is not None:
        for key in tuple(out.keys()):
            if key not in info.include:
                out.pop(key)

    if info.exclude_none:
        for key, value in tuple(out.items()):
            if value is None:
                out.pop(key, None)

    return out
