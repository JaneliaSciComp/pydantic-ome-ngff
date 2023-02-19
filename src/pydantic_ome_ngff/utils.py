from typing import Sequence, Dict, TypeVar, Any

T = TypeVar("T")


def census(values: Sequence[T]) -> Dict[T, int]:
    """
    Generate a dictionary of value : frequency pairs from a
    sequence of (hashable) values.
    """
    return {k: values.count(k) for k in set(values)}


def warning_on_one_line(
    message: str,
    category: Any,
    filename: str,
    lineno: int,
    file: Any = None,
    line: Any = None,
):
    """
    Format a warning so that it doesn't show source code
    """
    return f"{filename}:{lineno} {category.__name__}{message}\n"
