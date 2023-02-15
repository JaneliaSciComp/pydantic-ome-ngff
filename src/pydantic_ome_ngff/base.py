from pydantic import BaseModel
from typing import TypeVar, Sequence, Dict


class StrictBaseModel(BaseModel):
    """
    A pydantic basemodel that prevents extra fields.
    """

    class config:
        extra = "forbid"


T = TypeVar("T")


def census(values: Sequence[T]) -> Dict[T, int]:
    """
    Generate a dictionary of value : frequency pairs from a
    sequence of (hashable) values.
    """
    return {k: values.count(k) for k in set(values)}


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    """
    Format a warning so that it doesn't show source code
    """
    return f"{filename}:{lineno} {category.__name__}{message}\n"
