from pydantic_ome_ngff.v04.multiscales import Group
import zarr
url = "https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0062A/6001240.zarr"
zgroup = zarr.open(url)
group = Group.from_zarr(zgroup)
