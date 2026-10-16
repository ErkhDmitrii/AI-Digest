"""Метрики воронки дайджеста."""
import logging
from typing import Dict

import aiosqlite

from config.settings import settings

log = logging.getLogger("utils.metrics")


async def get_funnel_metrics() -> Dict[str, int]:
    """Возвращает метрики воронки: собрано → фильтр → дайджест → решение."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        # Всего собрано
        cursor = await db.execute("SELECT COUNT(*) FROM articles")
        collected = (await cursor.fetchone())[0]

        # Прошли фильтр
        cursor = await db.execute(
            "SELECT COUNT(*) FROM articles WHERE is_relevant = 1"
        )
        filtered = (await cursor.fetchone())[0]

        # В дайджесте
        cursor = await db.execute(
            "SELECT COUNT(*) FROM articles WHERE status = 'digested'"
        )
        in_digest = (await cursor.fetchone())[0]

        # Опубликовано
        cursor = await db.execute(
            "SELECT COUNT(*) FROM digests WHERE status = 'published'"
        )
        published = (await cursor.fetchone())[0]

    metrics = {
        "collected": collected,
        "filtered_relevant": filtered,
        "in_digest": in_digest,
        "published_digests": published,
    }
    log.info("Метрики: %s", metrics)
    return metrics
