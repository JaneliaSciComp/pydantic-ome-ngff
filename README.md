# pydantic-ome-ngff
## about
Pydantic models for OME-NGFF metadata. Versions 0.4 and the latest (v0.5-dev) are currently supported. 

supported metadata models: 

- [`multiscales`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/latest/multiscales.py) ([spec](https://ngff.openmicroscopy.org/latest/#multiscale-md))
- [`axes`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/latest/axes.py) ([spec](https://ngff.openmicroscopy.org/latest/#axes-md))
- [`coordinateTransformations`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/latest/coordinateTransformations.py) ([spec](https://ngff.openmicroscopy.org/latest/#trafo-md))
- [`plate`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/latest/plate.py) ([spec](https://ngff.openmicroscopy.org/latest/#plate-md))
- [`well`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/latest/well.py) ([spec](https://ngff.openmicroscopy.org/latest/#well-md))
- [`imageLabel`](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/src/pydantic_ome_ngff/latest/imageLabel.py) ([spec](https://ngff.openmicroscopy.org/latest/#label-md))

`omero` and `bioformats2raw` are not currently supported, but contributions adding
support for those models would be welcome.

## installation

```bash
pip install pydantic-ome-ngff
```

## development

1. clone this repo
2. install [poetry](https://python-poetry.org/)
3. run `poetry install --with dev` to get dev dependencies
4. run `pre-commit install` to install [pre-commit hooks](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/.pre-commit-config.yaml)