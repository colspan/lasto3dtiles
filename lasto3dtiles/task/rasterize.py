import json
import luigi
import open3d
import os

import lasto3dtiles.format.ply as plyutil
from lasto3dtiles.task.loadlas import LoadLas
from lasto3dtiles.util.rasterize import ndarray2img


class RasterizeLas(luigi.Task):
    input_filepath = luigi.Parameter()
    voxel_size = luigi.FloatParameter(default=0.1)
    output_dir = luigi.Parameter()
    output_format = luigi.Parameter(default='PNG')
    image_width = luigi.IntParameter(default=512)
    image_height = luigi.IntParameter(default=512)
    mirror_x = luigi.BoolParameter(default=False)
    skip_rate = luigi.FloatParameter(default=0.8)

    def requires(self):
        return LoadLas(self.input_filepath, self.mirror_x)

    def output(self):
        image_path = os.path.join(
            os.path.join(self.output_dir),
            '{}.{}'.format(os.path.basename(self.input_filepath), self.output_format.lower()))
        json_path = os.path.join(
            os.path.join(self.output_dir),
            '{}.json'.format(os.path.basename(self.input_filepath)))
        return {
            'json': luigi.LocalTarget(json_path),
            'image': luigi.LocalTarget(image_path)
        }

    def run(self):
        ply = plyutil.fromarray(
            self.input().load().toarray(skip_rate=self.skip_rate))

        # Voxel down sampling
        ply.voxel_down_sample(self.voxel_size)
        downdata = ply.toarray()

        img, xx, yy = ndarray2img(
            downdata, self.image_width, self.image_height)

        # write image
        output_target = self.output()['image']
        output_target.makedirs()
        img.save(output_target.path, format=self.output_format)

        # write metadata
        metadata = {
            'shape': list(xx.shape),
            'xx': xx.reshape(-1).tolist(),
            'yy': yy.reshape(-1).tolist(),
        }
        with self.output()['json'].open('w') as f_output:
            json.dump(metadata, f_output, ensure_ascii=False)
