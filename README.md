# pydantic-ome-ngff
## about
Pydantic models for OME-NGFF metadata. Only the latest version (v0.5-dev) of OME-NGFF is currently supported. 

supported metadata models: 

- [`multiscales`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/v05/multiscales.py) ([spec](https://ngff.openmicroscopy.org/latest/#multiscale-md))
- [`axes`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/v05/axes.py) ([spec](https://ngff.openmicroscopy.org/latest/#axes-md))
- [`coordinateTransformations`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/v05/coordinateTransformations.py) ([spec](https://ngff.openmicroscopy.org/latest/#trafo-md))
- [`plate`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/v05/plate.py) ([spec](https://ngff.openmicroscopy.org/latest/#plate-md))
- [`well`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/v05/well.py) ([spec](https://ngff.openmicroscopy.org/latest/#well-md))
- [`imageLabel`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/v05/imageLabel.py) ([spec](https://ngff.openmicroscopy.org/latest/#label-md))

`omero` and `bioformats2raw` are not supported. 

Note that these models will validate the contents of the various metadata fields, but cannot ensure that the metadata is structurally valid in the context of an array container -- e.g., these models cannot check that the number of axes in `multiscales.axes` matches the rank of arrays stored in the group bearing that `multiscales` metadata. This requires a representation of the group / array hierarchy as pydantic models, which is in progress.

## installation

```bash
pip install pydantic-ome-ngff
```

## development

1. clone this repo
2. install [poetry](https://python-poetry.org/)
3. run `poetry install --with dev` to get dev dependencies
4. run `pre-commit install` to install [pre-commit hooks](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/.pre-commit-config.yaml)