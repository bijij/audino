from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from rayquaza import Mediator, Message

__all__ = ("HealthTracker",)


class _HealthStatus(Message):
    __slots__: tuple[str, ...] = ("type", "healthy")

    def __init__(self, type: str, healthy: bool) -> None:
        self.type: str = type
        self.healthy: bool = healthy


class HealthTracker:
    """
    The HealthTracker class is used to track the health status of components.
    """

    def __init__(self) -> None:
        self._heath_states: dict[str, bool] = {}
        self._mediator: Mediator = Mediator()
        self._lock: asyncio.Lock = asyncio.Lock()

    async def get_health(self, type: str) -> bool:
        """|coro|

        Get the health status of a component.

        Parameters
        ----------
        type : :class:`str`
            The type of the component.

        Returns
        -------
        :class:`bool`
            The health status of the component.
        """
        async with self._lock:
            return self._heath_states.get(type, False)

    async def set_health(self, type: str, healthy: bool) -> None:
        """|coro|

        Set the health status of a component.

        Parameters
        ----------
        type : :class:`str`
            The type of the component.
        healthy : :class:`bool`
            The health status of the component.
        """
        async with self._lock:
            self._heath_states[type] = healthy

        message = _HealthStatus(type, healthy)
        await self._mediator.publish(message, wait=False)

    def subscribe(self, callback: Callable[[str, bool], Coroutine[Any, Any, None]]) -> None:
        """Subscribe to health status changes.

        Parameters
        ----------
        callback : :class:`Callable`
            The callback function that will be called when the health status of a component changes.
            The callback function should take two parameters: `type` and `healthy`.
        """

        async def _callback(message: _HealthStatus) -> None:
            await callback(message.type, message.healthy)

        self._mediator.create_subscription(_HealthStatus, _callback)
