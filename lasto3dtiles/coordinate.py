from math import sin, cos, tan, radians, pi, log, atan, sinh, degrees, sqrt


def deg_to_num(lat_deg, lon_deg, zoom):
    """
    degree to num
    """
    lat_rad = radians(lat_deg)
    n = 2.0 ** zoom
    xtile_f = (lon_deg + 180.0) / 360.0 * n
    ytile_f = (1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n
    xtile = int(xtile_f)
    ytile = int(ytile_f)
    pos_x = int((xtile_f - xtile) * 256)
    pos_y = int((ytile_f - ytile) * 256)
    return (xtile, ytile, pos_x, pos_y)


def num_to_deg(xtile, ytile, zoom):
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = atan(sinh(pi * (1 - 2 * ytile / n)))
    lat_deg = degrees(lat_rad)
    return (lat_deg, lon_deg)


wgs84a = 6378.137
wgs84f = 1.0 / 298.257223563
wgs84b = wgs84a * (1.0 - wgs84f)

f = 1 - wgs84b / wgs84a
eccsq = 1 - wgs84b * wgs84b / (wgs84a * wgs84a)
ecc = sqrt(eccsq)

EARTH_A = wgs84a
EARTH_B = wgs84b
EARTH_F = f
EARTH_Ecc = ecc
EARTH_Esq = eccsq


def deg_to_xyz(lat_deg, lon_deg, altitude):
    """
    http://www.oc.nps.edu/oc2902w/coord/geodesy.js
    lat,lon,altitude to xyz vector
    input:
        lat_deg      geodetic latitude in deg
        lon_deg      longitude in deg
        altitude     altitude in km
    output:
        returns vector x 3 long ECEF in km
    """
    clat = cos(radians(lat_deg))
    slat = sin(radians(lat_deg))
    clon = cos(radians(lon_deg))
    slon = sin(radians(lon_deg))

    _, rn, _ = radcur(lat_deg)

    ecc = EARTH_Ecc
    esq = ecc * ecc

    x = (rn + altitude) * clat * clon
    y = (rn + altitude) * clat * slon
    z = ((1 - esq) * rn + altitude) * slat

    return [x, y, z]


def radcur(lat_deg):
    """
        compute the radii at the geodetic latitude lat (in degrees)
        input:
                lat       geodetic latitude in degrees
        output:
                rrnrm     an array 3 long
                            r,  rn,  rm   in km
    """

    a = EARTH_A
    b = EARTH_B

    asq = a * a
    bsq = b * b
    eccsq = 1 - bsq / asq

    clat = cos(radians(lat_deg))
    slat = sin(radians(lat_deg))

    dsq = 1.0 - eccsq * slat * slat
    d = sqrt(dsq)

    rn = a / d
    rm = rn * (1.0 - eccsq) / dsq

    rho = rn * clat
    z = (1.0 - eccsq) * rn * slat
    rsq = rho * rho + z * z
    r = sqrt(rsq)

    return [r, rn, rm]


def estimate_transform_matrix(src, dst):
    import transforms3d._gohlketransforms as tf3d
    return tf3d.affine_matrix_from_points(src.T, dst.T, shear=False).T


class ProjectRangeDomain(object):
    def __init__(self, range_x, range_y, domain_lon, domain_lat):

        self.range_x = range_x
        self.range_y = range_y
        self.domain_lon = domain_lon
        self.domain_lat = domain_lat

        # global diff
        self.diff_x = max(self.range_x) - min(self.range_x)
        self.diff_y = max(self.range_y) - min(self.range_y)
        self.diff_lon = max(self.domain_lon) - min(self.domain_lon)
        self.diff_lat = max(self.domain_lat) - min(self.domain_lat)

    def proj_range2domain(self, x, y):
        return [
            (y - min(self.range_y)) /
            self.diff_y * self.diff_lat + min(self.domain_lat),
            (x - min(self.range_x)) /
            self.diff_x * self.diff_lon + min(self.domain_lon),
        ]

    def proj_domain2range(self, lat, lon):
        return [
            (lon - min(self.domain_lon)) /
            self.diff_lon * self.diff_x + min(self.range_x),
            (lat - min(self.domain_lat)) /
            self.diff_lat * self.diff_y + min(self.range_y),
        ]

import numpy as np
def get_height(lat_deg, lon_deg, nan=np.NAN):
    # return 0 # DEBUG
    import os
    import requests
    zoom = 15
    xtile, ytile, pos_x, pos_y = deg_to_num(lat_deg, lon_deg, zoom)
    url = 'http://cyberjapandata.gsi.go.jp/xyz/dem5a/{}/{}/{}.txt'.format(
        zoom, xtile, ytile)
    output_dir = os.path.join('var', 'cache')
    cache = os.path.join(
        output_dir, 'dem_{}_{}_{}.txt'.format(zoom, xtile, ytile))
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(cache):
        req = requests.get(url, stream=True)
        with open(cache, "wb") as f_out:
            for chunk in req.iter_content(chunk_size=1024):
                f_out.write(chunk)
    tile = np.empty((256, 256))
    with open(cache, "r") as f:
        try:
            for i, line in enumerate(f):
                tile[i, :] = np.array(
                    [float(x) if x != "e" else nan for x in line.strip().split(",")])
                # unit : km
                height = tile[pos_y, pos_x] / 1000
        except:
            height = 0
    return height
