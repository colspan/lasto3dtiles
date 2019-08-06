import numpy as np
import open3d


class PlyFile():
    def __init__(self, filename=None, data=None):
        if isinstance(data, open3d.geometry.PointCloud):
            pcd = data
        elif data is not None and hasattr(data, 'toarray'):
            pcd = ndarray2open3d(data.toarray())
        elif data is not None and isinstance(data, np.ndarray):
            pcd = ndarray2open3d(data)
        else:
            pcd = load(filename, data)
        self.obj = pcd

    def __del__(self):
        del self.obj

    def voxel_down_sample(self, voxel_size=0.1):
        old_obj = self.obj
        self.obj = open3d.geometry.voxel_down_sample(self.obj, voxel_size=voxel_size)
        del old_obj

    def save(self, filename):
        return dump(self.obj, filename)

    def toarray(self):
        return open3d2ndarray(self.obj)


def load(filename=None, data=None):
    return open3d.read_point_cloud(filename)


def dump(data, filename):
    if isinstance(data, open3d.geometry.PointCloud):
        pcd = data
    elif data is not None and hasattr(data, 'toarray'):
        pcd = ndarray2open3d(data.toarray())
    elif data is not None and isinstance(data, np.ndarray):
        pcd = ndarray2open3d(data)
    else:
        raise TypeError
    result = open3d.write_point_cloud(filename, pcd)
    if not result:
        raise Exception(
            'open3d write_point_cloud failed : {}'.format(filename))
    return result


def fromarray(data):
    return PlyFile(data=data)


def open3d2ndarray(data):
    points = np.asarray(data.points)
    intensity = np.zeros((points.shape[0], 1))
    colors = np.asarray(data.colors)
    return np.hstack([points, intensity, colors])


def ndarray2open3d(data):
    pcd = open3d.PointCloud()
    pcd.points = open3d.Vector3dVector(data[:, 0:3])
    if data.shape[0] == 0:
        return pcd
    # detect color schema
    if np.sum(data[0, 4:7]) > 0:
        colors = data[:, 4:7]
    else:
        colors = np.ndarray((data.shape[0], 3), dtype=np.float32)
        for i in range(3):
            colors[:, i] = data[:, 3]

    mean = np.mean(colors[:])
    if mean < 0.2:
        # enhance color
        for i in range(colors.shape[1]):
            colors[:, i] /= np.max(colors[:, i])

    pcd.colors = open3d.Vector3dVector(colors)
    return pcd
