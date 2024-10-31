import time
import asyncio
import threading
from typing import Any
from collections import deque


class SyncQueue:

    """
    동기 큐 버퍼.

    버퍼가 가득 찬 상태에서 새 아이템 삽입이 시도되면,
    기존 아이템 중 가장 오래된 것을 삭제한 후 삽입.
    경쟁 상태(race condition) 예방 포함.

    > buffer = SyncQueue()
    > buffer.get_maxsize()  # 최대 크기 출력
    > buffer.set_maxsize(5) # 최대 크기 설정(예:5)
    > buffer.put(item)      # 아이템 삽입하기
    > buffer.get(timeout=2) # 아이템 가져오기
    """

    def __init__(self, maxsize: int=1):
        self.mutex = threading.Lock()
        self.not_empty = threading.Condition(self.mutex)
        self._deque = deque()
        self._maxsize = maxsize

    def get_maxsize(self):
        return self._maxsize
    
    def set_maxsize(self, value: int=1):
        if value < 1:
            raise ValueError('The maxsize must be greater than 1.')
        with self.mutex:
            self._maxsize = value
            self._drop_items()

    def _put(self, item: Any):
        self._deque.append(item)

    def _get(self) -> Any:
        return self._deque.popleft()

    def _drop_items(self):
        while len(self._deque) >= self._maxsize:
            self._get()

    def put(self, item: Any):
        with self.mutex:
            self._drop_items()
            self._put(item)
            self.not_empty.notify()

    def get(self, timeout=30.0) -> Any:
        with self.not_empty:
            if timeout < 0:
                raise ValueError(
                    'The timeout must be greater than or equal to 0.')
            endtime = time.monotonic() + timeout
            while not self._deque:
                remaining = endtime - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('The task has timed out.')
                self.not_empty.wait(remaining)
            item = self._get()
            return item


class AsyncQueue:

    """
    비동기 큐 버퍼. 동기 큐 버퍼의 비동기 버전.

    버퍼가 가득 찬 상태에서 새 아이템 삽입이 시도되면,
    기존 아이템 중 가장 오래된 것을 삭제한 후 삽입.
    경쟁 상태(race condition) 예방 포함.

    > buffer = AsyncQueue()
    > await buffer.get_maxsize()  # 최대 크기 출력
    > await buffer.set_maxsize(5) # 최대 크기 설정(예:5)
    > await buffer.put(item)      # 아이템 삽입하기
    > await buffer.get(timeout=2) # 아이템 가져오기
    """

    def __init__(self, maxsize: int=1):
        self.mutex = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.mutex)
        self._deque = deque()
        self._maxsize = maxsize

    async def get_maxsize(self):
        return self._maxsize
    
    async def set_maxsize(self, value: int=1):
        if value < 1:
            raise ValueError('The maxsize must be greater than 1.')
        async with self.mutex:
            self._maxsize = value
            await self._drop_items()

    async def _put(self, item: Any):
        self._deque.append(item)

    async def _get(self) -> Any:
        return self._deque.popleft()

    async def _drop_items(self):
        while len(self._deque) >= self._maxsize:
            await self._get()

    async def put(self, item: Any):
        async with self.mutex:
            await self._drop_items()
            await self._put(item)
            self.not_empty.notify()

    async def get(self, timeout=30.0) -> Any:
        async with self.not_empty:
            if timeout < 0:
                raise ValueError(
                    'The timeout must be greater than or equal to 0.')
            try:
                await asyncio.wait_for(self.not_empty.wait(), timeout)
            except asyncio.TimeoutError:
                raise TimeoutError('The task has timed out.')
            item = await self._get()
            return item
