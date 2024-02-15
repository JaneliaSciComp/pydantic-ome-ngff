# pydantic-ome-ngff

[Pydantic](https://docs.pydantic.dev/latest/) models for [OME-NGFF](https://ngff.openmicroscopy.org/)

# About

This library aims to provide models for the the metadata objects and Zarr hierarchies described in the [OME-NGFF](https://ngff.openmicroscopy.org/) specifications.

# Reading Multiscale metadata

```python
# example data on S3-compatible cloud storage
from pydantic_ome_ngff.v04.multiscales import Group
import zarr
url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
zgroup = zarr.open(url)
group = Group.from_zarr(zgroup)

```
