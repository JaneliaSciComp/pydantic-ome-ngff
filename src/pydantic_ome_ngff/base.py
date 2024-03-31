from pydantic import BaseModel


class StrictBase(BaseModel, extra="forbid", frozen=True):
    """
    A frozen pydantic basemodel that refuses extra fields.
    """


class VersionedBase(BaseModel):
    """
    An internally versioned pydantic basemodel.
    """

    _version: str = "0.0"


class StrictVersionedBase(VersionedBase, StrictBase):
    """
    An internally versioned pydantic basemodel that refuses extra fields.
    """
