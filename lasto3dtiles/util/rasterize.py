import numpy as np
from PIL import Image
from scipy import ndimage, interpolate, signal


def ndarray2img(input, width=4096, height=4096, range_x=None, range_y=None):
    channel_num = 3  # RGB
    if range_x == None:
        range_x = (np.min(input[:, 0]), np.max(input[:, 0]))
    if range_y == None:
        range_y = (np.min(input[:, 1]), np.max(input[:, 1]))
    xx = np.linspace(np.min(range_x), np.max(range_x), width)
    yy = np.linspace(np.min(range_y), np.max(range_y), height)
    grid_x, grid_y = np.meshgrid(xx, yy)

    # Color
    colors = np.ndarray((input.shape[0], channel_num))
    # Detect color schema
    if np.sum(input[0, 4:7]) / 3 > np.sum(input[0, 3]):
        # RGB
        colors[:, 0:3] = input[:, 4:7]
    else:
        # Intensity to RGB
        for i in range(channel_num):
            colors[:, i] = input[:, 3]

    grids = []
    for i in range(channel_num):
        color = colors[:, i]
        grid = interpolate.griddata(
            input[:, 0:2], color, (grid_x, grid_y), method='nearest') * 255
        grids.append(grid.reshape(grid.shape + (1,)))

    # Alpha
    alpha, _, _ = np.histogram2d(input[:, 0], input[:, 1],
                                 range=[range_x, range_y],
                                 bins=[width, height])
    alpha[alpha > 0] = 255
    # alpha = signal.medfilt(alpha, kernel_size=3)
    alpha = alpha.reshape(width, height, 1)
    alpha = np.fliplr(ndimage.rotate(alpha, 270))
    grids.append(alpha)

    rgbarray = np.concatenate(grids, axis=2).astype(np.uint8)
    img = Image.fromarray(ndimage.rotate(np.fliplr(rgbarray), 180))
    return img, xx, yy
