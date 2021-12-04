import asyncio
from typing import Generic, TypeVar

_T = TypeVar('_T')


class WrappingLock(Generic[_T]):
    _lock: asyncio.Lock
    _value: _T

    def __init__(self, value: _T) -> None:
        self._lock = asyncio.Lock()
        self._value = value

    @property
    def value(self) -> _T:
        return self._value

    async def set_value(self, new_value: _T) -> None:
        async with self._lock:
            self._value = new_value

    async def __aenter__(self) -> _T:
        await self._lock.acquire()
        return self._value

    async def __aexit__(self, *args) -> None:
        self._lock.release()
