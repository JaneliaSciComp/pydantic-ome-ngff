from typing import List, Optional, Union

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_ome_ngff.base import VersionedBase

from pydantic_ome_ngff.v04.base import version
from pydantic_ome_ngff.v04.multiscales import MultiscaleGroup
from pydantic_zarr.v2 import GroupSpec, ArraySpec


class Image(BaseModel):
    path: str
    acquisition: Optional[int]


class WellMeta(VersionedBase):
    """
    Well metadata.
    See https://ngff.openmicroscopy.org/0.4/#well-md
    """

    # the version here as a private class attribute because the version is not required by the spec
    _version = version
    version: Optional[str] = version
    images: List[Image]


class WellAttributes(BaseModel):
    well: WellMeta


class WellGroup(
    GroupSpec[WellAttributes, Union[MultiscaleGroup, GroupSpec, ArraySpec]]
):
    @field_validator("members", mode="after")
    @classmethod
    def contains_well(
        cls, members: Union[MultiscaleGroup, GroupSpec, ArraySpec]
    ) -> Union[MultiscaleGroup, GroupSpec, ArraySpec]:
        """
        Check that .members contains a MultiscaleGroup
        """
        if not any(map(lambda v: isinstance(v, WellGroup), members.values())):
            raise ValidationError
        return members
