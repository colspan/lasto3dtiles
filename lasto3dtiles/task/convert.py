import glob
import luigi
import numpy as np
import open3d
import os

from functools import reduce

import lasto3dtiles.task.loadlas as loadlas
import lasto3dtiles.format.las as lasutil
import lasto3dtiles.format.ply as plyutil
import lasto3dtiles.format.pnts as pntsutil


class LasSetTo3dTiles(luigi.Task):
    input_dirname = luigi.Parameter()
    point_map_def = luigi.Parameter()
    output_dir = luigi.Parameter(default=os.path.join('var', '3dtiles'))
    voxel_size = luigi.FloatParameter(default=0.1)
    skip_rate = luigi.FloatParameter(default=0.1)
    mirror_x = luigi.BoolParameter(default=False)

    def __init__(self, *args, **kwargs):
        super(LasSetTo3dTiles, self).__init__(*args, **kwargs)
        self.input_files = glob.glob(
            os.path.join(self.input_dirname, '*.[lL][aA][sS]'))

    def requires(self):
        return map(lambda x: LasToPnts(x, mirror_x=self.mirror_x, voxel_size=self.voxel_size, skip_rate=self.skip_rate), self.input_files)

    def run(self):
        pass


class LasToPnts(luigi.Task):
    input_filename = luigi.Parameter()
    output_dir = luigi.Parameter(default=os.path.join('var', '3dtiles'))
    voxel_size = luigi.FloatParameter(default=0.1)
    skip_rate = luigi.FloatParameter(default=0.1)
    mirror_x = luigi.BoolParameter(default=False)

    def requires(self):
        return loadlas.LoadLas(self.input_filename, mirror_x=self.mirror_x)

    def output(self):
        return luigi.LocalTarget(os.path.join(self.output_dir, '{}.pnts'.format(os.path.basename(self.input_filename))))

    def run(self):
        ply = plyutil.fromarray(
            self.input().load().toarray(skip_rate=self.skip_rate))
        ply.voxel_down_sample(self.voxel_size)
        os.makedirs(self.output_dir, exist_ok=True)
        pntsutil.dump(ply.toarray(), self.output().path)
