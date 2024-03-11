# pydantic-ome-ngff

[Pydantic](https://docs.pydantic.dev/latest/) models for [OME-NGFF](https://ngff.openmicroscopy.org/)

# About

This library aims to provide models for the the metadata objects and Zarr hierarchies described in the [OME-NGFF](https://ngff.openmicroscopy.org/) specifications.

# Reading Multiscale metadata

```python
# example data served over http
from pydantic_ome_ngff.v04.multiscales import Group
import zarr
url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
zgroup = zarr.open(url)
# this is a Pydantic model of a Zarr group
group = Group.from_zarr(zgroup)
# it has an `attributes` attribute, which in turn has a `multiscales` attribute 
# which models the OME-NGFF multiscales metadata
print(group.attributes.multiscales)
"""
[
    MultiscaleMetadata(
        version='0.4',
        name=None,
        type=None,
        metadata=None,
        datasets=[
            Dataset(
                path='0',
                coordinateTransformations=(
                    VectorScale(
                        type='scale',
                        scale=[
                            1.0,
                            0.5002025531914894,
                            0.3603981534640209,
                            0.3603981534640209,
                        ],
                    ),
                ),
            ),
            Dataset(
                path='1',
                coordinateTransformations=(
                    VectorScale(
                        type='scale',
                        scale=[
                            1.0,
                            0.5002025531914894,
                            0.7207963069280418,
                            0.7207963069280418,
                        ],
                    ),
                ),
            ),
            Dataset(
                path='2',
                coordinateTransformations=(
                    VectorScale(
                        type='scale',
                        scale=[
                            1.0,
                            0.5002025531914894,
                            1.4415926138560835,
                            1.4415926138560835,
                        ],
                    ),
                ),
            ),
        ],
        axes=[
            Axis(name='c', type='channel', unit=None),
            Axis(name='z', type='space', unit='micrometer'),
            Axis(name='y', type='space', unit='micrometer'),
            Axis(name='x', type='space', unit='micrometer'),
        ],
        coordinateTransformations=None,
    )
]
"""
```
