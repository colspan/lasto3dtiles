import json
import numpy as np

def dump(data, filename):
    import struct
    points_length = len(data)

    version = 1
    tile_header_byte_length = 28

    positions_byte_length = points_length * 3 * np.float32().itemsize
    colors_byte_length = points_length * 3 * np.uint8().itemsize

    # json_header
    jsond = {}
    # length
    jsond['POINTS_LENGTH'] = points_length
    # # rtc
    # if self.rtc:
    #     jsond['RTC_CENTER'] = self.rtc
    # positions
    jsond['POSITION'] = {'byteOffset': 0}
    # colors
    jsond['RGB'] = {'byteOffset': positions_byte_length}
    json_str = json.dumps(jsond).replace(" ", "")
    n = len(json_str) + tile_header_byte_length
    json_str += ' ' * (4 - n % 4)
    json_header = bytes(json_str, 'utf-8')
    json_header_length = len(json_header)

    # write
    with open(filename, 'wb') as fp:
        fp.write(b'pnts')  # magic
        fp.write(
            struct.pack('<IIIIII',
                        version,
                        tile_header_byte_length + json_header_length +
                        positions_byte_length + colors_byte_length,
                        json_header_length,
                        positions_byte_length + colors_byte_length,
                        0,
                        0)
        )

        # pnts header
        fp.write(json_header)

        # points
        fp.write(data[:, 0:3].astype('<f').tobytes())

        # colors
        # detect color schema
        if np.sum(data[0, 4:7]) / 3 > np.sum(data[0, 3]):
            colors = data[:, 4:7]
        else:
            colors = np.ndarray((data.shape[0], 3))
            for i in range(3):
                colors[:, i] = data[:, 3]
        colors *= 256
        fp.write(colors.astype('<B').tobytes())
