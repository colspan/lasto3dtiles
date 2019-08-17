import luigi
from lasto3dtiles.task.convert import LasSetTo3dTiles, LasToPnts
from lasto3dtiles.task.rasterize import RasterizeLas


def command():
    luigi.run(local_scheduler=True)


if __name__ == "__main__":
    command()
