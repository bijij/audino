from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable, Coroutine
from typing import Any, overload

from rayquaza import Mediator, Message

__all__ = ("HealthTracker",)


_log = logging.getLogger(__name__)

class _HealthStatus(Message):
    __slots__: tuple[str, ...] = ("type", "healthy")

    def __init__(self, type: str, healthy: bool) -> None:
        self.type: str = type
        self.healthy: bool = healthy


class HealthTracker:
    """
    The HealthTracker class is used to track the health status of components.

    Parameters
    ----------
    mediator: Optional[:class:`Mediator`]
        The mediator to use for communication between components, if not provided an internal mediator will be used.
    mediator_channel: Optional[:class:`str`]
        The mediator channel to use for communication between components, if not provided an internal channel will be used.
    """

    @overload
    def __init__(self, mediator: None = ...) -> None:
        ...

    @overload
    def __init__(self, *, mediator: Mediator = ..., mediator_channel: str | None = ...) -> None:
        ...

    def __init__(self, mediator: Mediator | None = None, *, mediator_channel: str | None = None) -> None:
        self._heath_states: dict[str, bool] = {}
        self._mediator: Mediator = mediator or Mediator()
        self._mediator_channel: str = mediator_channel or os.urandom(16).hex()
        self._lock: asyncio.Lock = asyncio.Lock()

        _log.debug("Initailsed health tracker with mediator %s on channel %s", self._mediator, self._mediator_channel)

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

        _log.debug("Health status of %s set to %s", type, healthy)

        message = _HealthStatus(type, healthy)
        await self._mediator.publish(self._mediator_channel, message, wait=False)

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

        self._mediator.create_subscription(self._mediator_channel, _HealthStatus, _callback)
