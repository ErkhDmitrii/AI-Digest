"""Дедупликация статей (поиск дубликатов)."""
import hashlib
import logging

from db import database

log = logging.getLogger("pipeline.dedup")

def compute_text_hash(text: str) -> str:
    """Вычисляет хэш текста для поиска дубликатов."""
    if not text:
        return ""
    # Убираем лишние пробелы и приводим к нижнему регистру для стабильности
    clean_text = " ".join(text.lower().split())
    return hashlib.sha256(clean_text.encode('utf-8')).hexdigest()

async def is_duplicate_text(text_hash: str) -> bool:
    """Проверяет, есть ли уже в базе статья с таким же хэшем текста."""
    if not text_hash:
        return False

    async with database.pool.acquire() as conn:
        # Используем $1 (синтаксис PostgreSQL)
        row = await conn.fetchval(
            "SELECT id FROM articles WHERE text_hash = $1 LIMIT 1",
            text_hash
        )
        return row is not None
