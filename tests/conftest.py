from typing import Tuple, Any, Optional, Union, List, Dict
from pathlib import Path
import json

import requests


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


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

Jso = Optional[Union[List["Jso"], Dict[str, "Jso"], int, float, bool, str]]


class JsonLoader:
    def __init__(self, root: Union[str, Path]) -> None:
        self.root = FIXTURE_DIR.joinpath(root)

    def _path(self, path: Union[str, Path]) -> Path:
        p = self.root.joinpath(path)
        if not p.name.lower().endswith(".json"):
            p = p.with_name(p.name + ".json")
        return p

    def load_str(self, path: Union[str, Path]) -> str:
        return self._path(path).read_text()

    def load_obj(self, path: Union[str, Path]) -> dict[str, Jso]:
        return json.loads(self.load_str(path))
