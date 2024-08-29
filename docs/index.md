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

Version 0.4 of OME-NGFF has pretty extensive support, although my focus has been on getting the `Multiscales` metadata right; I don't use `well` or `plate` metadata, so it's highly likely that I have missed something there. I have not put a lot of effort into supporting `0.5-dev`, as it's not clear when that version will be released, or even what will be in it, but contributions to rectify this are welcome. If you find something that I didn't implement correctly, please [open an issue](https://github.com/JaneliaSciComp/pydantic-ome-ngff/issues).

### Array data

This library only models the *structure* of a Zarr hierarchy, i.e. the layout of Zarr groups and arrays, and their metadata; it provides no functionality for efficiently reading or writing data from Zarr arrays. Use [`zarr-python`](https://github.com/zarr-developers/zarr-python) or [`tensorstore`](https://google.github.io/tensorstore/) for getting data in and out of Zarr arrays.

# Examples

## Reading a Multiscale group

This example demonstrates how to use the [`Group`](./api/v04/multiscale.md#Group) class defined in [`pydantic_ome_ngff.v04.multiscale`](./api/v04/multiscale.md) to model a multiscale group from cloud storage.

```python
from pydantic_ome_ngff.v04.multiscale import Group
import zarr
# example data served over http
url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"

# open the Zarr group
zgroup = zarr.open(url, mode='r')

# group_model is a `GroupSpec`, i.e. a Pydantic model of a Zarr group
group_model = Group.from_zarr(zgroup)

# it has an `attributes` attribute, which in turn has a `multiscales` attribute 
# which models the OME-NGFF multiscales metadata
multi_meta = group_model.attributes.multiscales
print(multi_meta)
"""
(
    MultiscaleMetadata(
        version='0.4',
        name=None,
        type=None,
        metadata=None,
        datasets=(
            Dataset(
                path='0',
                coordinateTransformations=(
                    VectorScale(
                        type='scale',
                        scale=(
                            1.0,
                            0.5002025531914894,
                            0.3603981534640209,
                            0.3603981534640209,
                        ),
                    ),
                ),
            ),
            Dataset(
                path='1',
                coordinateTransformations=(
                    VectorScale(
                        type='scale',
                        scale=(
                            1.0,
                            0.5002025531914894,
                            0.7207963069280418,
                            0.7207963069280418,
                        ),
                    ),
                ),
            ),
            Dataset(
                path='2',
                coordinateTransformations=(
                    VectorScale(
                        type='scale',
                        scale=(
                            1.0,
                            0.5002025531914894,
                            1.4415926138560835,
                            1.4415926138560835,
                        ),
                    ),
                ),
            ),
        ),
        axes=(
            Axis(name='c', type='channel', unit=None),
            Axis(name='z', type='space', unit='micrometer'),
            Axis(name='y', type='space', unit='micrometer'),
            Axis(name='x', type='space', unit='micrometer'),
        ),
        coordinateTransformations=None,
    ),
)
"""

# to get the Zarr arrays referenced by the multiscale metadata, we access them by name from the Zarr group.
arrays = [zgroup[d.path] for d in multi_meta[0].datasets]
print(arrays)
"""
[<zarr.core.Array '/0' (2, 236, 275, 271) uint16 read-only>, <zarr.core.Array '/1' (2, 236, 137, 135) uint16 read-only>, <zarr.core.Array '/2' (2, 236, 68, 67) uint16 read-only>]
"""
```

## Creating a multiscale group from arrays

`pydantic-ome-ngff` provides a direct way to create multiscale metadata from a collection of arrays accompanied by spatial metadata. Note that the data in these arrays will not be accessed -- the arrays are used to create models of Zarr arrays, and so their `shape` and `dtype` attributes are necessary, and other attributes (like `chunks`, if present), can be used to template the resulting Zarr arrays.

The basic workflow is as follows:

 1. Use in-memory numpy or dask arrays and spatial metadata to instantiate a model of the OME-NGFF multiscale Zarr group we want to create. This model contains attributes and models of Zarr arrays, but no array data (which keeps the model lightweight). 
 2. Serialize the model to a storage backend, which will create the Zarr groups and arrays defined by the model, along with their metadata. 
3. Write array data to the newly created Zarr arrays, using a method that suits your application. 

```python
from pydantic_ome_ngff.v04.multiscale import MultiscaleGroup
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
group_model = MultiscaleGroup.from_arrays(
    axes=axes,
    paths=paths,
    arrays=arrays,
    scales=scales,
    translations=translations,
    chunks=store_chunks,
    compressor=None)

print(group_model.model_dump())
"""
{
    'zarr_version': 2,
    'attributes': {
        'multiscales': (
            {
                'version': '0.4',
                'datasets': (
                    {
                        'path': 's0',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': (1.0, 2.0, 2.0, 2.0)},
                            {
                                'type': 'translation',
                                'translation': (0.0, 0.0, 0.0, 0.0),
                            },
                        ),
                    },
                    {
                        'path': 's1',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': (2.0, 4.0, 4.0, 4.0)},
                            {
                                'type': 'translation',
                                'translation': (0.5, 1.0, 1.0, 1.0),
                            },
                        ),
                    },
                ),
                'axes': (
                    {'name': 't', 'type': 'time', 'unit': 'second'},
                    {'name': 'z', 'type': 'space', 'unit': 'nanometer'},
                    {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
                    {'name': 'x', 'type': 'space', 'unit': 'nanometer'},
                ),
            },
        )
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
    'multiscales': (
        {
            'version': '0.4',
            'datasets': (
                {
                    'path': 's0',
                    'coordinateTransformations': (
                        {'type': 'scale', 'scale': (1.0, 2.0, 2.0, 2.0)},
                        {'type': 'translation', 'translation': (0.0, 0.0, 0.0, 0.0)},
                    ),
                },
                {
                    'path': 's1',
                    'coordinateTransformations': (
                        {'type': 'scale', 'scale': (2.0, 4.0, 4.0, 4.0)},
                        {'type': 'translation', 'translation': (0.5, 1.0, 1.0, 1.0)},
                    ),
                },
            ),
            'axes': (
                {'name': 't', 'type': 'time', 'unit': 'second'},
                {'name': 'z', 'type': 'space', 'unit': 'nanometer'},
                {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
                {'name': 'x', 'type': 'space', 'unit': 'nanometer'},
            ),
        },
    )
}
"""
```

## Creating a multiscale group directly

It's also possible to create a multiscale group without using the `from_arrays` method demonstrated in the previous example, but it's a bit more involved.

```python
from pydantic_zarr.v2 import ArraySpec
from pydantic_ome_ngff.v04.multiscale import MultiscaleGroup, MultiscaleMetadata, create_dataset, MultiscaleGroupAttrs
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
dtypes = ('uint8', 'uint8')

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

datasets = tuple(create_dataset(p, s, t) for p, s, t in zip(paths, scales, translations))

multiscales = MultiscaleMetadata(
    datasets=datasets,
    axes=axes)

attributes = MultiscaleGroupAttrs(multiscales=(multiscales,))
members = {p: ArraySpec(shape=s, dtype=d, chunks=store_chunks) for p,s,d in zip(paths, shapes, dtypes)}

group = MultiscaleGroup(attributes=attributes, members = members)

print(group.model_dump())
"""
{
    'zarr_version': 2,
    'attributes': {
        'multiscales': (
            {
                'version': '0.4',
                'datasets': (
                    {
                        'path': 's0',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': (1.0, 2.0, 2.0, 2.0)},
                            {
                                'type': 'translation',
                                'translation': (0.0, 0.0, 0.0, 0.0),
                            },
                        ),
                    },
                    {
                        'path': 's1',
                        'coordinateTransformations': (
                            {'type': 'scale', 'scale': (2.0, 4.0, 4.0, 4.0)},
                            {
                                'type': 'translation',
                                'translation': (0.5, 1.0, 1.0, 1.0),
                            },
                        ),
                    },
                ),
                'axes': (
                    {'name': 't', 'type': 'time', 'unit': 'second'},
                    {'name': 'z', 'type': 'space', 'unit': 'nanometer'},
                    {'name': 'y', 'type': 'space', 'unit': 'nanometer'},
                    {'name': 'x', 'type': 'space', 'unit': 'nanometer'},
                ),
            },
        )
    },
    'members': {
        's0': {
            'zarr_version': 2,
            'attributes': {},
            'shape': (10, 10, 10, 10),
            'chunks': (1, 2, 2, 2),
            'dtype': '|u1',
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
            'dtype': '|u1',
            'fill_value': 0,
            'order': 'C',
            'filters': None,
            'dimension_separator': '/',
            'compressor': None,
        },
    },
}
"""
```

### Hierarchy modelling 

Multiple OME-NGFF multiscale groups can be stored together in Zarr groups.
The OME-NGFF specification doesn't define explicit rules for such collections, so this library does not contain
data structures to specifically model "Zarr group that contains OME-NGFF groups". But it is not hard to model this 
using a combination of `pydantic-ome-ngff` and `pydantic-zarr`:

```python
from pydantic_zarr.v2 import GroupSpec
from pydantic_ome_ngff.v04 import MultiscaleGroup, Axis
from typing import Union, Any
import numpy as np
import zarr

# define a model of a Zarr group that contains MultiscaleGroups
# this relies on the fact that GroupSpec is generic with two 
# type parameters. the first type parameter is for the attributes, 
# which we set to `Any`, and the second type parameter is for the members of the group
# which we set to the union of GroupSpec and MultiscaleGroup. 
GroupOfMultiscales = GroupSpec[Any, Union[GroupSpec, MultiscaleGroup]]
axes = [Axis(name='x', type='space'), Axis(name='y', type='space')]

m_group_a = MultiscaleGroup.from_arrays(
    arrays = [np.zeros((10,10))],
    paths=['s0'],
    axes=axes,
    scales=[[1,1]],
    translations=[[0,0]])

m_group_b = MultiscaleGroup.from_arrays(
    arrays = [np.zeros((20,20))],
    paths=['s0'],
    axes=axes,
    scales=[[10,10]],
    translations=[[5,5]])

group_c = GroupSpec(attributes={'foo': 10})

groups = {'a': m_group_a, 'b': m_group_b, 'c': group_c}

store = zarr.MemoryStore()

multi_image_group = GroupOfMultiscales(members=groups)
zgroup = multi_image_group.to_zarr(store, path='multi_image_group')

print(GroupOfMultiscales.from_zarr(zgroup).model_dump())
"""
{
    'zarr_version': 2,
    'attributes': {},
    'members': {
        'a': {
            'zarr_version': 2,
            'attributes': {
                'multiscales': (
                    {
                        'version': '0.4',
                        'datasets': (
                            {
                                'path': 's0',
                                'coordinateTransformations': (
                                    {'type': 'scale', 'scale': (1, 1)},
                                    {'type': 'translation', 'translation': (0, 0)},
                                ),
                            },
                        ),
                        'axes': (
                            {'name': 'x', 'type': 'space'},
                            {'name': 'y', 'type': 'space'},
                        ),
                    },
                )
            },
            'members': {
                's0': {
                    'zarr_version': 2,
                    'attributes': {},
                    'shape': (10, 10),
                    'chunks': (10, 10),
                    'dtype': '<f8',
                    'fill_value': 0.0,
                    'order': 'C',
                    'filters': None,
                    'dimension_separator': '/',
                    'compressor': {'id': 'zstd', 'level': 3, 'checksum': False},
                }
            },
        },
        'b': {
            'zarr_version': 2,
            'attributes': {
                'multiscales': (
                    {
                        'version': '0.4',
                        'datasets': (
                            {
                                'path': 's0',
                                'coordinateTransformations': (
                                    {'type': 'scale', 'scale': (10, 10)},
                                    {'type': 'translation', 'translation': (5, 5)},
                                ),
                            },
                        ),
                        'axes': (
                            {'name': 'x', 'type': 'space'},
                            {'name': 'y', 'type': 'space'},
                        ),
                    },
                )
            },
            'members': {
                's0': {
                    'zarr_version': 2,
                    'attributes': {},
                    'shape': (20, 20),
                    'chunks': (20, 20),
                    'dtype': '<f8',
                    'fill_value': 0.0,
                    'order': 'C',
                    'filters': None,
                    'dimension_separator': '/',
                    'compressor': {'id': 'zstd', 'level': 3, 'checksum': False},
                }
            },
        },
        'c': {'zarr_version': 2, 'attributes': {'foo': 10}, 'members': {}},
    },
}
"""
```



## Data validation

This library attempts to detect invalid OME-NGFF containers and provide useful error messages when something is broken. The following examples illustrate a few ways in which OME-NGFF metadata can be broken, and what the error messages look like.

```python
from pydantic import ValidationError
from pydantic_zarr.v2 import ArraySpec
from pydantic_ome_ngff.v04.multiscale import MultiscaleGroup
from pydantic_ome_ngff.v04.axis import Axis
import numpy as np

arrays = np.zeros((10,10)), np.zeros((5,5))
scales = ((1,1), (2,2))
translations = ((0,0), (0.5, 0.5))
paths = ('s0','s1')
axes = (
    Axis(name='y', unit='nanometer', type='space'),
    Axis(name='x', unit='nanometer', type='space')
)

# create a valid multiscale group
group_model = MultiscaleGroup.from_arrays(arrays, paths=paths, axes=axes, scales=scales, translations=translations)

# convert that group to a dictionary, so we can break it
group_model_missing_array = group_model.model_dump()

# remove one of the arrays. this invalidates the multiscale metadata
group_model_missing_array['members'].pop('s0')

try:
    MultiscaleGroup(**group_model_missing_array)
except ValidationError as e:
    print(e)
    """
    1 validation error for MultiscaleGroup
      Value error, Dataset s0 was specified in multiscale metadata, but no array with that name was found in the hierarchy. All arrays referenced in multiscale metadata must be contained in the group. [type=value_error, input_value={'zarr_version': 2, 'attr...3, 'checksum': False}}}}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2.8/v/value_error
    """

group_model_wrong_array = group_model.model_dump()

# insert an array with incorrect dimensionality
group_model_wrong_array['members']['s0'] = ArraySpec.from_array(np.arange(10)).model_dump()

try:
    MultiscaleGroup(**group_model_wrong_array)
except ValidationError as e:
    print(e)
    """
    1 validation error for MultiscaleGroup
      Value error, Transform type='scale' scale=(1, 1) has dimensionality 2, which does not match the dimensionality of the array found in this group at s0 (1). Transform dimensionality must match array dimensionality. [type=value_error, input_value={'zarr_version': 2, 'attr...3, 'checksum': False}}}}, input_type=dict]
        For further information visit https://errors.pydantic.dev/2.8/v/value_error
    """
```