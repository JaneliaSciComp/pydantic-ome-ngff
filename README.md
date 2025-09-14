# pydantic-ome-ngff

> [!IMPORTANT]
> this project is archived!
> see [ome-zarr-models-py](https://ome-zarr-models-py.readthedocs.io/en/stable/) for a contemporary replacement.

## about
Pydantic models for [OME-NGFF](https://ngff.openmicroscopy.org/) metadata. Version [0.4](https://ngff.openmicroscopy.org/0.4/index.html) is supported. Read the documentation for the latest release [here](https://janeliascicomp.github.io/pydantic-ome-ngff/).

## installation

```bash
pip install -U pydantic-ome-ngff
```

## development

1. clone this repo
2. install [hatch](https://hatch.pypa.io/latest/)
4. run `pre-commit install` to install [pre-commit hooks](https://github.com/JaneliaSciComp/pydantic-ome-ngff/blob/main/.pre-commit-config.yaml)
5. edit the code
6. run tests with `hatch run:test run`
