import asyncio
from collections import defaultdict
from typing import AsyncGenerator

_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


async def init_event_bus() -> None:
    pass


async def publish(event_type: str, payload: dict) -> None:
    event = {"type": event_type, "payload": payload}
    for queue in _subscribers[event_type]:
        await queue.put(event)
    for queue in _subscribers["*"]:
        await queue.put(event)


async def subscribe(event_type: str = "*") -> AsyncGenerator[dict, None]:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[event_type].append(queue)
    try:
        while True:
            yield await queue.get()
    finally:
        _subscribers[event_type].remove(queue)
