# -*- coding:utf-8 -*-

"""
Las to 3dtiles converter
"""

import glob
import json
import luigi
import math
import numpy as np
import open3d
import os

from functools import reduce

import lasto3dtiles.task.loadlas as loadlas
import lasto3dtiles.format.las as lasutil
import lasto3dtiles.format.ply as plyutil
import lasto3dtiles.format.pnts as pntsutil
import lasto3dtiles.util.coordinate as coordutil


class LasSetTo3dTiles(luigi.Task):
    """
    Convert multiple LAS files to 3dtiles format.

    Args:
        :param input_dir: Input directory that containes LAS files (format 1.0)
        :param point_map_def: JSON file that defines corresponding points between LAS files' local coordinates (``xy``) and geographic longitude / latitude (``lonlat``)

        E.g.
        ...code-block:: json
            {
                "xy": [
                    [
                    -71016.5,
                    -142633.0625
                    ],
                    [
                    -70975.96875,
                    -142653.90625
                    ],
                    [
                    -70978.46875,
                    -142668.03125
                    ]
                ],
                "lonlat": [
                    [
                    137.7247106283903,
                    34.711804475805295
                    ],
                    [
                    137.725145816803,
                    34.711618717192835
                    ],
                    [
                    137.7251169830561,
                    34.71148973322244
                    ]
                ]
            }

        :param output_dir: Output directory for converted 3Dtiles format files
        :param voxel_size: Voxel size for resampling. Default value is ``0.1``.
        :param skip_rate: Skip rate for fetching points from LAS files. Default value is ``0.1``.
        :param mirror_x: Mirror x axis for right hand system (``xy`` in ``point_map_def`` is supporsed to be mirrored)
        :param shift_z: Offset for z axis. Unit is kilo meter. Default is ``0.020``.
    """
    input_dir = luigi.Parameter()
    point_map_def = luigi.Parameter()
    output_dir = luigi.Parameter(default=os.path.join('var', '3dtiles'))
    voxel_size = luigi.FloatParameter(default=0.1)
    skip_rate = luigi.FloatParameter(default=0.1)
    mirror_x = luigi.BoolParameter(default=False)
    shift_z = luigi.FloatParameter(default=0.020)

    def __init__(self, *args, **kwargs):
        super(LasSetTo3dTiles, self).__init__(*args, **kwargs)
        self.input_files = glob.glob(
            os.path.join(self.input_dir, '*.[lL][aA][sS]'))

    def requires(self):
        return map(lambda x: LasToPnts(x,
                                       mirror_x=self.mirror_x,
                                       voxel_size=self.voxel_size,
                                       output_dir=self.output_dir,
                                       skip_rate=self.skip_rate), self.input_files)

    def output(self):
        # TODO set relative path
        return luigi.LocalTarget(os.path.join(self.output_dir, 'tileset.json'))

    def run(self):
        height_range = (0, 50)  # TODO parameterize

        # 各LASファイルの範囲を読む
        las_targets = [x.requires().output().load() for x in self.requires()]
        x_mins = [np.min(d.obj.X * d.obj.header.scale[0] +
                         d.obj.header.offset[0]) for d in las_targets]
        x_maxs = [np.max(d.obj.X * d.obj.header.scale[0] +
                         d.obj.header.offset[0]) for d in las_targets]
        y_mins = [np.min(d.obj.Y * d.obj.header.scale[1] +
                         d.obj.header.offset[1]) for d in las_targets]
        y_maxs = [np.max(d.obj.Y * d.obj.header.scale[1] +
                         d.obj.header.offset[1]) for d in las_targets]

        # 点群と緯度経度の対応を読む
        with open(self.point_map_def, 'r') as f_input:
            point_map = json.load(f_input)

        # print(point_map)
        src = np.asarray([[x, y, 0, 1]
                          for x, y in point_map['xy']])  # TODO set height from las

        z_offset = self.shift_z
        dst_xyz = np.asarray([[v * 1000 for v in coordutil.deg_to_xyz(
            lat, lon, coordutil.get_height(lat, lon, nan=0) - z_offset)] + [1] for lon, lat in point_map['lonlat']])
        # print(dst_xyz)
        mat_xyz = coordutil.estimate_transform_matrix(
            src[:, 0:3], dst_xyz[:, 0:3])

        # Tangent Plane で線形近似するための値域を取得する
        range_x = [min(x_mins), max(x_maxs)]
        range_y = [min(y_mins), max(y_maxs)]
        # print(x_mins, x_maxs, y_mins, y_maxs)
        domain_min = np.dot(
            np.array([range_x[0], range_y[0], 0, 1]), mat_xyz)
        domain_max = np.dot(
            np.array([range_x[1], range_y[1], 0, 1]), mat_xyz)
        # print(domain_min, domain_max)

        import pymap3d
        domain_lonlat_min = pymap3d.ecef2geodetic(
            *tuple(domain_min[0:3].tolist()))
        domain_lonlat_max = pymap3d.ecef2geodetic(
            *tuple(domain_max[0:3].tolist()))
        domain_lon = [domain_lonlat_min[1], domain_lonlat_max[1]]
        domain_lat = [domain_lonlat_min[0], domain_lonlat_max[0]]
        # print(domain_lon, domain_lat)

        def getTileChildren(pnts_task):
            las_target = pnts_task.requires().output().load()
            data = las_target.obj.points['point']
            x_min = np.min(data['X'])
            x_max = np.max(data['X'])
            y_min = np.min(data['Y'])
            y_max = np.max(data['Y'])

            domain_min = np.dot(
                np.array([x_min, y_min, 0, 1]), mat_xyz)
            domain_max = np.dot(
                np.array([x_max, x_max, 0, 1]), mat_xyz)
            domain_latlon_min = pymap3d.ecef2geodetic(
                *tuple(domain_min[0:3].tolist()))
            domain_latlon_max = pymap3d.ecef2geodetic(
                *tuple(domain_max[0:3].tolist()))

            south, west, _ = domain_latlon_min
            north, east, _ = domain_latlon_max

            target_tile = os.path.basename(pnts_task.output().path)

            tileset_def = {
                'boundingVolume': {
                    'region': [
                        # TODO calcurate accurate bounding box
                        # west / 180.0 * math.pi,  # lon_min
                        # south / 180.0 * math.pi,  # lat_min
                        # east / 180.0 * math.pi,  # lon_max
                        # north / 180.0 * math.pi,  # lat_max
                        min(domain_lon) / 180.0 * math.pi,  # lon_min
                        min(domain_lat) / 180.0 * math.pi,  # lat_min
                        max(domain_lon) / 180.0 * math.pi,  # lon_max
                        max(domain_lat) / 180.0 * math.pi,  # lat_max
                        min(height_range),
                        max(height_range),
                    ]
                },
                'geometricError': 0,
                'refine': 'ADD',
                'content': {
                    'url': target_tile,
                },
            }
            return tileset_def

        tileset_root = {
            'transform': list(mat_xyz.reshape(-1)),
            'boundingVolume': {
                'region': [
                    min(domain_lon) / 180.0 * math.pi,  # lon_min
                    min(domain_lat) / 180.0 * math.pi,  # lat_min
                    max(domain_lon) / 180.0 * math.pi,  # lon_max
                    max(domain_lat) / 180.0 * math.pi,  # lat_max
                    min(height_range),
                    max(height_range),
                ]
            },
            'geometricError': 50,
            'refine': 'REPLACE',
            'children': [getTileChildren(x) for x in self.requires()],
        }
        tileset_def = {
            'asset': {
                'version': '0.0'
            },
            'root': tileset_root,
        }
        with self.output().open('w') as f_output:
            json.dump(tileset_def, f_output, indent=True, ensure_ascii=False)


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
