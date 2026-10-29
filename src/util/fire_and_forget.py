import asyncio
from collections.abc import Coroutine
from typing import Any

# Keeps a reference so the event loop cannot garbage-collect a running task
_tasks: set[asyncio.Task[Any]] = set()


def fire_and_forget(coro: Coroutine[Any, Any, Any]) -> None:
    """Runs a coroutine without awaiting it, as the TypeScript code did.

    Failures are logged rather than surfaced to the caller.
    """
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    task.add_done_callback(_log_failure)


def _log_failure(task: asyncio.Task[Any]) -> None:
    if task.cancelled():
        return
    error = task.exception()
    if error is not None:
        print("Background task failed:", error)
