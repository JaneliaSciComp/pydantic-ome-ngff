# pydantic-ome-ngff

[Pydantic](https://docs.pydantic.dev/latest/) models for [OME-NGFF](https://ngff.openmicroscopy.org/)

# About

This library aims to provide models for the the metadata objects and Zarr hierarchies described in the [OME-NGFF](https://ngff.openmicroscopy.org/) specifications.

# Examples

## Reading Multiscale metadata

This example demonstrates how to use the `Group` class defined in `pydantic_ome_ngff.v04.multiscales` to model a multiscale group.

```python
from pydantic_ome_ngff.v04.multiscales import Group
import zarr
# example data served over http
url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"

# open the Zarr group
zgroup = zarr.open(url)

# group_model is a `GroupSpec`, i.e. a Pydantic model of a Zarr group
group_model = Group.from_zarr(zgroup)

# it has an `attributes` attribute, which in turn has a `multiscales` attribute 
# which models the OME-NGFF multiscales metadata
multi_meta = group_model.attributes.multiscales
print(multi_meta)
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

# to get the Zarr arrays referenced by the multiscale metadata, we access them by name from the Zarr group.
arrays = [zgroup[d.path] for d in multi_meta[0].datasets]
print(arrays)
"""
[<zarr.core.Array '/0' (2, 236, 275, 271) uint16>, <zarr.core.Array '/1' (2, 236, 137, 135) uint16>, <zarr.core.Array '/2' (2, 236, 68, 67) uint16>]
"""
```

## Creating multiscale metadata

`pydantic-ome-ngff` provides simple way to create multiscale metadata from a collection of arrays accompanied by spatial metadata.

```python
from pydantic_ome_ngff.v04.multiscales import Group
from pydantic_ome_ngff.v04.axis import Axis
import numpy as np
import zarr

# define the axes
axes = [
    Axis(name='t', unit='second', type='time'),
    Axis(name='z', unit='nanometer', type='space'),
    Axis(name='y', unit='nanometer', type='space'),
    Axis(name='x', unit='nanometer', type='space')
]

ndim = len(axes)

# the chunk size we want to use for our Zarr arrays
store_chunks = (1, 2, 2, 2)

# simulate a multiscale pyramid
shapes = (10,) * ndim, (5,) * ndim
arrays = []
scales = []
translations = []
paths = []

# define the base scaling and translation
scale_base = [1.0, 2.0, 2.0, 2.0]
trans_base = [0.0, 0.0, 0.0, 0.0]

for idx, s in enumerate(shapes):
    arrays.append(np.zeros(s))
    # power of 2 downsampling per-axis for each image
    scales.append(np.multiply(2 ** idx, scale_base))
    # downsampling-induced translation per-axis for each image
    translations.append(
        np.multiply(scale_base, 2 ** (idx - 1)),
    )

    if idx > 0:
        translations[-1] += np.sum(translations[:-1], axis=0)

    # name the arrays s0, s1, s2
    paths.append(f's{idx}')

# this is now a complete model of the Zarr group
group_model = Group.from_arrays(
    axes=axes,
    paths=paths,
    arrays=arrays,
    scales=scales,
    translations=translations,
    chunks=store_chunks)

print(group_model.model_dump())
"""
{
    'zarr_version': 2,
    'attributes': {
        'multiscales': [
            {
                'version': '0.4',
                'name': None,
                'type': None,
                'metadata': None,
                'datasets': [
                    {
                        'path': 's0',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': [1.0, 2.0, 2.0, 2.0]},
                            {
                                'type': 'translation',
                                'translation': [0.5, 1.0, 1.0, 1.0],
                            },
                        ),
                    },
                    {
                        'path': 's1',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': [2.0, 4.0, 4.0, 4.0]},
                            {
                                'type': 'translation',
                                'translation': [1.5, 3.0, 3.0, 3.0],
                            },
                        ),
                    },
                ],
                'axes': [
                    {'name': 't', 'type': 'time', 'unit': 'second'},
                    {'name': 'z', 'type': 'space', 'unit': 'nanometer'},
                    {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
                    {'name': 'x', 'type': 'space', 'unit': 'nanometer'},
                ],
                'coordinateTransformations': None,
            }
        ]
    },
    'members': {
        's0': {
            'zarr_version': 2,
            'attributes': {},
            'shape': (10, 10, 10, 10),
            'chunks': (1, 2, 2, 2),
            'dtype': '<f8',
            'fill_value': 0,
            'order': 'C',
            'filters': None,
            'dimension_separator': '/',
            'compressor': None,
        },
        's1': {
            'zarr_version': 2,
            'attributes': {},
            'shape': (5, 5, 5, 5),
            'chunks': (1, 2, 2, 2),
            'dtype': '<f8',
            'fill_value': 0,
            'order': 'C',
            'filters': None,
            'dimension_separator': '/',
            'compressor': None,
        },
    },
}
"""

# to actually do something useful with this model, we have to serialize it to storage

# make an in-memory zarr store for demo purposes
# with real data, you would use `zarr.storage.DirectoryStore` or `zarr.storage.FSStore`
store = zarr.MemoryStore()
path = 'foo'
stored_group = group_model.to_zarr(store, path='foo')

# check that the expected arrays are present
# no data has been written to these arrays, you must do that separately.
# e.g., stored_group[s0] = arrays[0]
print(stored_group.tree())
"""
foo
 ├── s0 (10, 10, 10, 10) float64
 └── s1 (5, 5, 5, 5) float64
"""

# check that the expected attributes are present
print(stored_group.attrs.asdict())
"""
{
    'multiscales': [
        {
            'version': '0.4',
            'name': None,
            'type': None,
            'metadata': None,
            'datasets': [
                {
                    'path': 's0',
                    'coordinateTransformations': (
                        {'type': 'scale', 'scale': [1.0, 2.0, 2.0, 2.0]},
                        {'type': 'translation', 'translation': [0.5, 1.0, 1.0, 1.0]},
                    ),
                },
                {
                    'path': 's1',
                    'coordinateTransformations': (
                        {'type': 'scale', 'scale': [2.0, 4.0, 4.0, 4.0]},
                        {'type': 'translation', 'translation': [1.5, 3.0, 3.0, 3.0]},
                    ),
                },
            ],
            'axes': [
                {'name': 't', 'type': 'time', 'unit': 'second'},
                {'name': 'z', 'type': 'space', 'unit': 'nanometer'},
                {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
                {'name': 'x', 'type': 'space', 'unit': 'nanometer'},
            ],
            'coordinateTransformations': None,
        }
    ]
}
"""



```