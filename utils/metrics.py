"""Метрики воронки дайджеста."""
import logging
from typing import Dict

from db import database

log = logging.getLogger("utils.metrics")


async def get_funnel_metrics() -> Dict[str, int]:
    """Возвращает метрики воронки: собрано → фильтр → дайджест → решение."""
    
    # Используем пул подключений к PostgreSQL
    async with database.pool.acquire() as conn:
        # Всего собрано
        collected = await conn.fetchval("SELECT COUNT(*) FROM articles")


        filtered = await conn.fetchval(
            "SELECT COUNT(*) FROM articles WHERE is_relevant = TRUE"
        )

        # В дайджесте
        in_digest = await conn.fetchval(
            "SELECT COUNT(*) FROM articles WHERE status = 'digested'"
        )

        # Опубликовано
        published = await conn.fetchval(
            "SELECT COUNT(*) FROM digests WHERE status = 'published'"
        )


    metrics = {
        "collected": collected or 0,
        "filtered_relevant": filtered or 0,
        "in_digest": in_digest or 0,
        "published_digests": published or 0,
    }
    
    log.info("Метрики: %s", metrics)
    return metrics
