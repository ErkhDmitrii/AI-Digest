"""Дедупликация: по URL (SHA-256) + по тексту (SimHash)."""
import logging
from typing import Optional

import aiosqlite

from config.settings import settings

log = logging.getLogger("pipeline.dedup")


def compute_text_hash(text: str) -> str:
    """Вычисляет SimHash текста."""
    try:
        from simhash import Simhash
        return str(Simhash(text[:5000]).value)
    except Exception:
        # Fallback на простой хеш если simhash недоступен
        import hashlib
        return hashlib.md5(text[:5000].encode()).hexdigest()


async def is_duplicate_text(text_hash: str) -> bool:
    """Проверяет, есть ли уже статья с таким text_hash в БД."""
    if not text_hash:
        return False
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM articles WHERE text_hash = ?", (text_hash,)
        )
        count = await cursor.fetchone()
        return count[0] > 0 if count else False
