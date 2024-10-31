import sys
from pathlib import Path
sys.path.append(
    str(
        Path(__file__).parents[1].absolute()
    )
)
import json

import cv2

from mycam.camera import Camera


def get_source():
    config_file = str(
        Path(__file__).parent.absolute()/'config.json'
    )
    with open(config_file, mode='r', encoding='utf-8') as f:
        config = json.load(f)
    cam_source = config['cam_source']
    return cam_source


if __name__ == '__main__':
    cam_source = get_source()

    cam = Camera()
    cam.buffer_size = 5
    cam.open(cam_source)

    while True:
        frame = cam.read_frame()

        cv2.imshow('result', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cv2.destroyAllWindows()
    cam.close()