import pydantic_ome_ngff.v04.axis as axisV04

AxisType = axisV04.AxisType

class Axis(axisV04.Axis):
    """
    Axis metadata.
    See https://ngff.openmicroscopy.org/latest/#axes-md

    Note: this metadata is unchanged from version 0.4 of the spec.
    """
