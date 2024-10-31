import asyncio
import threading
from typing import Callable


class SingleThreadTask:

    def __init__(self):
        self._task = None
        self._stop = False

    def is_alive(self) -> bool:
        return self._task is not None and self._task.is_alive()

    def _job(self, target, *args):
        try:
            while not self._stop:
                target(*args)
        except Exception:
            raise

    def start(self, target: Callable, args=None):
        if self.is_alive():
            raise RuntimeError('The thread is already started.')
        if args is None:
            args = []
        self._task = threading.Thread(target=self._job, args=[target, *args])
        self._task.start()

    def stop(self):
        if not self.is_alive():
            raise RuntimeError('The thread is already stopped.')
        self._stop = True
        self._task.join()
        self._stop = False


class SingleAsyncTask:

    def __init__(self):
        self._task = None
        self._stop = False

    def is_alive(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _job(self, target, *args):
        try:
            while not self._stop:
                await target(*args)
                await asyncio.sleep(0)
        except Exception:
            raise

    async def start(self, target: Callable, args=None):
        if self.is_alive():
            raise RuntimeError('The async task is already started.')
        if args is None:
            args = []
        self._task = asyncio.create_task(self._job(target, *args))

    async def stop(self):
        if not self.is_alive():
            raise RuntimeError('The async task is already stopped.')
        self._stop = True
        await self._task
        self._stop = False