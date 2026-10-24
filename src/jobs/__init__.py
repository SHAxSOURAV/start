import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.jobs.otp_cleanup_job import cleanup_expired_otp_fields
from src.jobs.soft_delete_cleanup_job import purge_expired_soft_deleted_accounts
from src.util.logger import logger

scheduler: AsyncIOScheduler | None = None


async def _cleanup_tick() -> None:
    try:
        await asyncio.gather(
            cleanup_expired_otp_fields("activation"),
            cleanup_expired_otp_fields("verification"),
        )
    except Exception as error:
        logger.error(f"Error removing expired code: {error}")


async def _purge_soft_deleted_tick() -> None:
    try:
        await purge_expired_soft_deleted_accounts()
    except Exception as error:
        logger.error(f"Error purging 30-day soft deleted accounts: {error}")


def start_jobs() -> None:
    """Called after the DB connection is established, so importing app modules
    (e.g. in tests) never starts background jobs."""
    global scheduler

    scheduler = AsyncIOScheduler()
    scheduler.add_job(_cleanup_tick, CronTrigger.from_crontab("* * * * *"))
    # Run soft-deleted accounts purge daily at midnight
    scheduler.add_job(_purge_soft_deleted_tick, CronTrigger.from_crontab("0 0 * * *"))
    scheduler.start()

    logger.info("Background jobs started (OTP cleanup + 30-day soft delete purge)")


def stop_jobs() -> None:
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=False)
        scheduler = None
