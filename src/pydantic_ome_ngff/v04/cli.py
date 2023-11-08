import sys
from pydantic_ome_ngff.v04.multiscales import MultiscaleGroup
import zarr
from pydantic import ValidationError
from rich import print_json, print

if __name__ == "__main__":
    path: str = sys.argv[1]
    group = zarr.open(path, mode="r")
    try:
        result = MultiscaleGroup.from_zarr(group).model_dump_json(indent=2)
        print_json(result)
    except ValidationError as e:
        result = e
        print(result)
