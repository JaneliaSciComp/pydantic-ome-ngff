from pydantic import BaseModel

class StrictBaseModel(BaseModel):
    """
    A pydantic basemodel that prevents extra fields.
    """

    class config:
        extra = "forbid"


def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    """
    Format a warning so that it doesn't show source code
    """
    return f'{filename}:{lineno} {category.__name__}{message}\n'