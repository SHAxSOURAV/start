import asyncio
import signal
import sys
from functools import partial

import uvicorn

from src.config import config
from src.connection.connect_db import connect_db, disconnect_db
from src.connection.connect_redis import connect_redis, disconnect_redis
from src.connection.socket import main_server, sio
from src.jobs import start_jobs, stop_jobs
from src.util.logger import error_logger, logger

SHUTDOWN_TIMEOUT_S = 10

is_shutting_down = False
_server: uvicorn.Server | None = None


async def shutdown(exit_code: int, reason: str) -> None:
    global is_shutting_down
    if is_shutting_down:
        return
    is_shutting_down = True

    logger.info(f"Shutting down ({reason})...")

    # Hard-kill fallback in case a connection refuses to close
    loop = asyncio.get_running_loop()
    force_exit = loop.call_later(SHUTDOWN_TIMEOUT_S, _force_exit, exit_code)

    try:
        stop_jobs()
        await sio.shutdown()
        if _server is not None:
            _server.should_exit = True
        await disconnect_redis()
        await disconnect_db()
        logger.info("Shutdown complete")
    except Exception as error:
        error_logger.error(f"Error during shutdown: {error}")
    finally:
        force_exit.cancel()
        sys.exit(exit_code)


def _force_exit(exit_code: int) -> None:
    error_logger.error("Forced shutdown after timeout")
    import os

    os._exit(exit_code)


def _handle_loop_exception(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    """The unhandledRejection / uncaughtException equivalent."""
    error = context.get("exception") or context.get("message")
    error_logger.error(f"Unhandled Exception: {error}")
    asyncio.create_task(shutdown(1, "unhandledException"))


def _schedule_shutdown(reason: str) -> None:
    asyncio.create_task(shutdown(0, reason))


async def main() -> None:
    global _server

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(_handle_loop_exception)

    for sig, reason in ((signal.SIGTERM, "SIGTERM"), (signal.SIGINT, "SIGINT")):
        try:
            loop.add_signal_handler(sig, partial(_schedule_shutdown, reason))
        except NotImplementedError:
            # Windows: uvicorn installs its own handlers
            pass

    try:
        await connect_db()
        logger.info("DB Connected Successfully")

        await connect_redis()

        server_config = uvicorn.Config(
            main_server,
            host=config.base_url,
            port=int(config.port),
            log_config=None,
            lifespan="off",
        )
        _server = uvicorn.Server(server_config)

        logger.info(f"App listening on http://{config.base_url}:{config.port}")

        start_jobs()

        await _server.serve()
    except Exception as err:
        error_logger.error(f"Main Function Error: {err}")
        sys.exit(1)
    finally:
        stop_jobs()
        await disconnect_redis()
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())
