from typing import Any

import requests


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
