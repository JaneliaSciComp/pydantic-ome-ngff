from pydantic import BaseModel, Extra


class StrictBase(BaseModel, extra=Extra.forbid):
    """
    A pydantic basemodel that refuses extra fields.
    """

    ...


class VersionedBase(BaseModel):
    """
    An internally versioned pydantic basemodel.
    """

    _version: str = "0.0"


class StrictVersionedBase(VersionedBase, StrictBase):
    """
    An internally versioned pydantic basemodel that refuses extra fields.
    """

    ...
