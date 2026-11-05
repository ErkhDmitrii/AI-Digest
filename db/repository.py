"""CRUD-операции с базой данных PostgreSQL."""
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

import asyncpg

from config.settings import settings
from db import database
from db.models import Article, Digest

log = logging.getLogger("db.repository")

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

async def save_article(
    source_name: str, source_type: str, title: str, text: str, url: str,
    published_at: Optional[datetime] = None, is_whitelist: bool = False,
    text_hash: Optional[str] = None,
) -> bool:
    url_h = _url_hash(url)


    if published_at:
        if published_at.tzinfo is None:
            # Если дата без пояса, считаем, что это UTC
            published_at = published_at.replace(tzinfo=timezone.utc)
        else:
            # Если с поясом, конвертируем в UTC
            published_at = published_at.astimezone(timezone.utc)

    try:
        async with database.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO articles 
                   (source_name, source_type, title, text, url, url_hash, text_hash, published_at, is_whitelist)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                source_name, source_type, title, text, url, url_h, text_hash, published_at, is_whitelist
            )
        return True
    except asyncpg.UniqueViolationError:
        log.debug("Дубликат URL: %s", url)
        return False

async def get_unfiltered_articles() -> List[Article]:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM articles WHERE status = 'new' ORDER BY collected_at")
        return [_row_to_article(r) for r in rows]

async def update_article_filter(
    article_id: int, is_relevant: bool, reason: str,
    categories: Optional[List[str]] = None, confidence: Optional[float] = None,
):
    cat_str = json.dumps(categories, ensure_ascii=False) if categories else None
    status = "filtered_relevant" if is_relevant else "filtered_out"
    async with database.pool.acquire() as conn:
        await conn.execute(
            """UPDATE articles SET 
               status = $1, is_relevant = $2, relevance_reason = $3,
               categories = $4, category_confidence = $5
               WHERE id = $6""",
            status, is_relevant, reason, cat_str, confidence, article_id
        )

async def get_articles_for_digest(categories: Optional[List[str]] = None) -> dict:
    async with database.pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM articles WHERE status = 'filtered_relevant' ORDER BY published_at DESC")

    result = {cat: [] for cat in settings.CATEGORIES}
    for row in rows:
        art = _row_to_article(row)
        if art.categories:
            for cat in art.categories:
                if cat in result:
                    result[cat].append(art)
    return result

async def mark_articles_used():
    async with database.pool.acquire() as conn:
        await conn.execute("UPDATE articles SET status = 'digested' WHERE status = 'filtered_relevant'")
        log.info("Статьи помечены как использованные (digested)")

async def save_digest(issue_number: int, content: str) -> int:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO digests (issue_number, content) VALUES ($1, $2) RETURNING id",
            issue_number, content
        )
        return row["id"]

async def update_digest_decision(digest_id: int, decision: str, final_text: Optional[str] = None):
    async with database.pool.acquire() as conn:
        if final_text:
            await conn.execute(
                "UPDATE digests SET status = $1, admin_decision = $2, final_text = $3 WHERE id = $4",
                "decided", decision, final_text, digest_id
            )
        else:
            await conn.execute(
                "UPDATE digests SET status = $1, admin_decision = $2 WHERE id = $3",
                "decided", decision, digest_id
            )

async def mark_digest_published(digest_id: int):
    async with database.pool.acquire() as conn:
        await conn.execute(
            "UPDATE digests SET status = 'published', published_at = $1 WHERE id = $2",
            datetime.now(), digest_id
        )

async def get_next_issue_number() -> int:
    async with database.pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM digests")
        return (count or 0) + 1

async def get_digest_by_id(digest_id: int) -> Optional[Digest]:
    async with database.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM digests WHERE id = $1", digest_id)
        if row:
            return Digest(
                id=row["id"], issue_number=row["issue_number"], created_at=row["created_at"],
                content=row["content"], status=row["status"], admin_decision=row["admin_decision"],
                final_text=row["final_text"], published_at=row["published_at"],
            )
        return None

def _row_to_article(row) -> Article:
    categories = None
    if row["categories"]:
        try:
            categories = json.loads(row["categories"]) if isinstance(row["categories"], str) else row["categories"]
        except Exception:
            categories = None
    return Article(
        id=row["id"], source_name=row["source_name"], source_type=row["source_type"],
        title=row["title"], text=row["text"], url=row["url"], url_hash=row["url_hash"],
        text_hash=row["text_hash"], published_at=row["published_at"], collected_at=row["collected_at"],
        status=row["status"], is_relevant=row["is_relevant"],
        relevance_reason=row["relevance_reason"], categories=categories,
        category_confidence=row["category_confidence"], is_whitelist=row["is_whitelist"],
    )
