from pydantic_ome_ngff.v04 import Axis


def test_axis_serialization() -> None:
    ax = Axis(name="foo", unit=None, type=None)
    assert ax.model_dump() == {"name": ax.name}
    assert ax.model_dump(exclude={"name"}) == {}
