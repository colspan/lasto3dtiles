import numpy as np
from laspy.file import File

def load(filename):
    inFile = File(filename, mode = "r")
    point_records = inFile.points

    cnt = len(inFile)
    ptdata = np.zeros( (cnt, 7), dtype=np.float64)

    colmap = [
        'X',
        'Y',
        'Z',
        'intensity',
        'red',
        'green',
        'blue',
    ]
    for i, col in enumerate(colmap):
        ptdata[:, i] = point_records['point'][col].astype(np.float64)

    return ptdata
