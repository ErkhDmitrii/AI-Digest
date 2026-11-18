"""Планировщик задач — APScheduler (AsyncIOScheduler)."""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import settings
from pipeline.orchestrator import run_full_pipeline

log = logging.getLogger("bot.scheduler")


def init_scheduler() -> AsyncIOScheduler:
    """Создаёт и настраивает AsyncIOScheduler с задачами."""
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)

    # Задача: периодический сбор и фильтрация.
    if settings.COLLECT_INTERVAL_MINUTES > 0:
        collect_trigger = IntervalTrigger(
            minutes=settings.COLLECT_INTERVAL_MINUTES)
        interval_label = f"{settings.COLLECT_INTERVAL_MINUTES} мин"
    else:
        collect_trigger = IntervalTrigger(
            hours=settings.COLLECT_INTERVAL_HOURS)
        interval_label = f"{settings.COLLECT_INTERVAL_HOURS} ч"

    scheduler.add_job(
        scheduled_collect,
        collect_trigger,
        id="scheduled_collect",
        name="Сбор и фильтрация",
        replace_existing=True,
    )

    scheduler.add_job(
        scheduled_digest,
        CronTrigger(
            day_of_week=settings.DIGEST_DAY_OF_WEEK,
            hour=settings.DIGEST_HOUR, 
            minute=0
        ),
        id="scheduled_digest",
        name="Дайджест",
        replace_existing=True,
    )

    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    day_label = days[settings.DIGEST_DAY_OF_WEEK] if 0 <= settings.DIGEST_DAY_OF_WEEK <= 6 else str(settings.DIGEST_DAY_OF_WEEK)

    log.info(
        "Jobs: collect каждые %s, digest раз в неделю (%s) в %02d:00 (%s)",
        interval_label, day_label, settings.DIGEST_HOUR, settings.TIMEZONE
    )

    return scheduler


async def scheduled_collect():
    """Задача: сбор данных и фильтрация."""
    log.info("=== Запуск задачи scheduled_collect ===")
    try:
        from collectors.manager import run_collectors_once
        from pipeline.filter import filter_and_categorize

        await run_collectors_once()
        stats = await filter_and_categorize()
        log.info("scheduled_collect завершён: %s", stats)

    except Exception as e:
        log.error("Ошибка в scheduled_collect: %s", e)


async def scheduled_digest():
    """Задача: сборка дайджеста и отправка черновика в админ-чат."""
    log.info("=== Запуск задачи scheduled_digest ===")
    try:
        from bot.handlers import send_draft_to_admin

        digest_text = await run_full_pipeline()
        await send_draft_to_admin(digest_text)

    except Exception as e:
        log.error("Ошибка в scheduled_digest: %s", e)
