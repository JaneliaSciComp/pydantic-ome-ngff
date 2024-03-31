from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

import pytest
import requests
from zarr.storage import MemoryStore, FSStore, NestedDirectoryStore
import py


def fetch_schemas(version: str, schema_name: str) -> tuple[Any, Any]:
    """
    Get the relaxed and strict schemas for a given version of the spec.
    """
    base_schema = requests.get(
        f"https://ngff.openmicroscopy.org/{version}/schemas/strict_{schema_name}.schema"
    ).json()
    strict_schema = requests.get(
        f"https://ngff.openmicroscopy.org/{version}/schemas/{schema_name}.schema"
    ).json()
    return base_schema, strict_schema


@pytest.fixture(scope="function")
def memory_store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture(scope="function")
def fsstore_local(tmpdir: py.path.local) -> FSStore:
    return FSStore(str(tmpdir))


@pytest.fixture(scope="function")
def nested_directory_store(tmpdir: py.path.local) -> NestedDirectoryStore:
    return NestedDirectoryStore(tmpdir)
