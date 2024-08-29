import pytest
import pydantic
from pydantic_ome_ngff.base import FrozenBase, VersionedBase, SkipNoneBase


def test_frozen_base() -> None:
    class X(FrozenBase):
        x: int

    f = X(x=10)
    with pytest.raises(pydantic.ValidationError, match="Instance is frozen"):
        f.x = 100  # type: ignore


def test_versioned_base() -> None:
    class X(VersionedBase): ...

    assert X()._version == "0.0"


def test_noneskipbase() -> None:
    class X(SkipNoneBase):
        _skip_if_none = ("a", "b")
        a: int | None
        b: int
        c: int

    instance = X(a=None, b=10, c=10)
    assert instance.model_dump() == {"b": 10, "c": 10}
    assert instance.model_dump(include={"b"}) == {"b": 10}
    assert instance.model_dump(exclude={"b"}) == {"c": 10}
