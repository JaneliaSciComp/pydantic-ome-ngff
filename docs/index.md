# pydantic-ome-ngff

[Pydantic](https://docs.pydantic.dev/latest/) models for [OME-NGFF](https://ngff.openmicroscopy.org/)

# About

This library aims to model the metadata objects and Zarr hierarchies described in the [OME-NGFF](https://ngff.openmicroscopy.org/) specifications, with an emphasis on the core multiscale metadata. 

You can use this library to:

- Read existing OME-NGFF data
- Create your own OME-NGFF data  

See the [reading](#reading-a-multiscale-group) and [writing](#creating-a-multiscale-group) examples for basic usage. 

The base Pydantic models for Zarr groups and arrays used in this library are defined in [`pydantic-zarr`](https://janelia-cellmap.github.io/pydantic-zarr/)

## Limitations

### Supported versions

Version 0.4 of OME-NGFF has pretty extensive support, although my focus has been on getting the `Multiscales` metadata right; I don't use `well` or `plate` metadata, so it's likely that I have missed something there. I have not put a lot of effort into supporting `0.5-dev`, as it's not clear when that version will be released, or even what will be in it, but contributions to rectify this are welcome. 

### Array data

This library only models the *structure* of a Zarr hierarchy, i.e. the layout of Zarr groups and arrays, and their metadata; it provides no functionality for efficiently reading or writing large Zarr arrays. Consider [`tensorstore`](https://google.github.io/tensorstore/) or [`dask`](https://www.dask.org/) for this purpose.


# Examples

## Reading a Multiscale group

This example demonstrates how to use the `Group` class defined in `pydantic_ome_ngff.v04.multiscale` to model an existing multiscale group.

```python
from pydantic_ome_ngff.v04.multiscale import Group
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

## Creating a multiscale group

`pydantic-ome-ngff` provides simple way to create multiscale metadata from a collection of arrays accompanied by spatial metadata. 

The basic workflow is as follows:

 1. Use in-memory numpy or dask arrays and spatial metadata to instantiate a model of the OME-NGFF multiscale Zarr group we want to create. This model contains attributes and models of Zarr arrays, but no array data (which keeps the model lightweight). 
 2. Serialize the model to a storage backend, which will create the Zarr groups and arrays defined by the model, along with their metadata. 
3. Write array data to the newly created Zarr arrays, using a method that suits your application. 

```python
from pydantic_ome_ngff.v04.multiscale import Group
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
arrays = [np.zeros(s) for s in shapes]

# arrays will be named s0, s1, etc
paths = [f's{idx}' for idx in range(len(shapes))]

# downsampling by 2 in each axis
scales = [
    [1.0, 2.0, 2.0, 2.0],
    [2.0, 4.0, 4.0, 4.0],
]

# s0 is at the origin; s1 is at the offset induced by downsampling
translations = [
    [0.0, 0.0, 0.0, 0.0],
    [0.5, 1.0, 1.0, 1.0]
]

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
                                'translation': [0.0, 0.0, 0.0, 0.0],
                            },
                        ),
                    },
                    {
                        'path': 's1',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': [2.0, 4.0, 4.0, 4.0]},
                            {
                                'type': 'translation',
                                'translation': [0.5, 1.0, 1.0, 1.0],
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

# to do something useful with this model, we have to serialize it to storage
# we make an in-memory zarr store for demo purposes
# with real data, you would use `zarr.storage.DirectoryStore` or `zarr.storage.FSStore`
store = zarr.MemoryStore()
path = 'foo'
stored_group = group_model.to_zarr(store, path='foo')

# check that the expected arrays are present
print(stored_group.tree())
"""
foo
 ├── s0 (10, 10, 10, 10) float64
 └── s1 (5, 5, 5, 5) float64
"""

# NOTE:
# no data has been written to these arrays, you must do that separately.
# e.g., stored_group[s0] = arrays[0]

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
                        {'type': 'translation', 'translation': [0.0, 0.0, 0.0, 0.0]},
                    ),
                },
                {
                    'path': 's1',
                    'coordinateTransformations': (
                        {'type': 'scale', 'scale': [2.0, 4.0, 4.0, 4.0]},
                        {'type': 'translation', 'translation': [0.5, 1.0, 1.0, 1.0]},
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