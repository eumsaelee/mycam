import time
import threading

import cv2
import numpy as np

from mycam.buffer import SyncQueue
from mycam.task import SingleThreadTask


class Capture:

    def __init__(self):
        self.mutex = threading.Lock()
        self._cap = cv2.VideoCapture()
        self._cap.setExceptionMode(enable=True)

    def open(self, source, api_preference=cv2.CAP_ANY):
        try:
            with self.mutex:
                self._cap.open(source, api_preference)
        except Exception as e:
            raise ConnectionError(
                'Failed to open the camera source.') from e

    def close(self):
        with self.mutex:
            self._cap.release()

    def read_frame(self, timeout=30.0) -> np.ndarray:
        if timeout < 0:
            raise ValueError(
                'The timeout must be greater than or equal to 0.')
        endtime = time.monotonic() + timeout
        while True:
            try:
                with self.mutex:
                    _, frame = self._cap.read()
                return frame
            except Exception as e:
                remaining = endtime - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('The task has timed out.') from e
                time.sleep(0.1)


class Camera:

    def __init__(self):
        self._capture = Capture()
        self._buffer = SyncQueue()
        self._buffer_task = SingleThreadTask()

    @property
    def buffer_size(self):
        return self._buffer.get_maxsize()

    @buffer_size.setter
    def buffer_size(self, value: int=1):
        self._buffer.set_maxsize(value)

    def _capturing(self):
        self._buffer.put(self._capture.read_frame())

    def open(self, source, api_preference=cv2.CAP_ANY):
        self._capture.open(source, api_preference)
        self._buffer_task.start(self._capturing)

    def close(self):
        self._buffer_task.stop()
        self._capture.close()

    def read_frame(self, timeout=30.0) -> np.ndarray:
        return self._buffer.get(timeout)
