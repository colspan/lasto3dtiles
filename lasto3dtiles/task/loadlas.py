import luigi
import lasto3dtiles.format.las as lasutil


class LasTarget(luigi.LocalTarget):
    def __init__(self, path, mirror_x=False):
        super(LasTarget, self).__init__(path)
        self.mirror_x = mirror_x

    def load(self):
        data = lasutil.LasFile(self.path)
        if self.mirror_x:
            data.obj.points['point']['X'] *= -1
        return data


class LoadLas(luigi.ExternalTask):
    input_path = luigi.Parameter()
    skip_rate = luigi.FloatParameter(default=0.8)
    mirror_x = luigi.BoolParameter(default=False)

    def output(self):
        return LasTarget(self.input_path, mirror_x=self.mirror_x)
