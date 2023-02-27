from collections import Counter
from typing import Dict, Any, Sequence, Tuple, Hashable

import requests


def duplicates(values: Sequence[Hashable]) -> Dict[Hashable, int]:
    """
    Takes a sequence of hashable elements and returns a dict where the keys are the
    elements of the input that occurred at least once, and the values are the
    frequencies of those elements.
    """
    counts = Counter(values)
    return {k: v for k, v in counts.items() if v > 1}


def fetch_schemas(version: str, schema_name: str) -> Tuple[Any, Any]:
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
