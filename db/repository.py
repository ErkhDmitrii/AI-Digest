"""CRUD-операции с базой данных."""
import hashlib
import json
import logging
from datetime import datetime
from typing import List, Optional

import aiosqlite

from config.settings import settings
from db.models import Article, Digest

log = logging.getLogger("db.repository")


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


async def save_article(
    source_name: str,
    source_type: str,
    title: str,
    text: str,
    url: str,
    published_at: Optional[datetime] = None,
    is_whitelist: bool = False,
    text_hash: Optional[str] = None,
) -> bool:
    """Сохраняет статью. Возвращает True если новая, False если дубликат URL."""
    url_h = _url_hash(url)
    async with aiosqlite.connect(settings.DB_PATH) as db:
        try:
            await db.execute(
                """INSERT INTO articles 
                   (source_name, source_type, title, text, url, url_hash, text_hash, 
                    published_at, is_whitelist)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (source_name, source_type, title, text, url, url_h, text_hash,
                 published_at, int(is_whitelist))
            )
            await db.commit()
            log.debug("Сохранена статья: %s", url)
            return True
        except aiosqlite.IntegrityError:
            log.debug("Дубликат URL: %s", url)
            return False


async def get_unfiltered_articles() -> List[Article]:
    """Возвращает статьи со статусом 'new' для фильтрации."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM articles WHERE status = 'new' ORDER BY collected_at"
        )
        rows = await cursor.fetchall()
        return [_row_to_article(r) for r in rows]


async def update_article_filter(
    article_id: int,
    is_relevant: bool,
    reason: str,
    categories: Optional[List[str]] = None,
    confidence: Optional[float] = None,
):
    """Обновляет результат фильтрации и категоризации."""
    cat_str = json.dumps(
        categories, ensure_ascii=False) if categories else None
    status = "filtered_relevant" if is_relevant else "filtered_out"
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            """UPDATE articles SET 
               status = ?, is_relevant = ?, relevance_reason = ?,
               categories = ?, category_confidence = ?
               WHERE id = ?""",
            (status, int(is_relevant), reason, cat_str, confidence, article_id)
        )
        await db.commit()


async def get_articles_for_digest(categories: Optional[List[str]] = None) -> dict:
    """Возвращает статьи для дайджеста, сгруппированные по категориям."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM articles WHERE status = 'filtered_relevant' ORDER BY published_at DESC"
        )
        rows = await cursor.fetchall()

    result = {cat: [] for cat in settings.CATEGORIES}
    for row in rows:
        art = _row_to_article(row)
        if art.categories:
            for cat in art.categories:
                if cat in result:
                    result[cat].append(art)
    return result


async def mark_articles_used():
    """Отмечает статьи как использованные в дайджесте."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "UPDATE articles SET status = 'digested' WHERE status = 'filtered_relevant'"
        )
        await db.commit()


async def save_digest(issue_number: int, content: str) -> int:
    """Сохраняет черновик дайджеста. Возвращает ID."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO digests (issue_number, content) VALUES (?, ?)",
            (issue_number, content)
        )
        await db.commit()
        return cursor.lastrowid


async def update_digest_decision(digest_id: int, decision: str, final_text: Optional[str] = None):
    """Обновляет решение модератора."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        if final_text:
            await db.execute(
                "UPDATE digests SET status = ?, admin_decision = ?, final_text = ? WHERE id = ?",
                ("decided", decision, final_text, digest_id)
            )
        else:
            await db.execute(
                "UPDATE digests SET status = ?, admin_decision = ? WHERE id = ?",
                ("decided", decision, digest_id)
            )
        await db.commit()


async def mark_digest_published(digest_id: int):
    """Отмечает дайджест как опубликованный."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute(
            "UPDATE digests SET status = 'published', published_at = ? WHERE id = ?",
            (datetime.now().isoformat(), digest_id)
        )
        await db.commit()


async def get_next_issue_number() -> int:
    """Возвращает следующий номер выпуска."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM digests")
        count = await cursor.fetchone()
        return (count[0] if count else 0) + 1


async def get_digest_by_id(digest_id: int) -> Optional[Digest]:
    """Возвращает дайджест по ID."""
    async with aiosqlite.connect(settings.DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM digests WHERE id = ?", (digest_id,))
        row = await cursor.fetchone()
        if row:
            return Digest(
                id=row["id"],
                issue_number=row["issue_number"],
                created_at=row["created_at"],
                content=row["content"],
                status=row["status"],
                admin_decision=row["admin_decision"],
                final_text=row["final_text"],
                published_at=row["published_at"],
            )
        return None


def _row_to_article(row) -> Article:
    categories = None
    if row["categories"]:
        try:
            categories = json.loads(row["categories"])
        except (json.JSONDecodeError, TypeError):
            categories = None
    return Article(
        id=row["id"],
        source_name=row["source_name"],
        source_type=row["source_type"],
        title=row["title"],
        text=row["text"],
        url=row["url"],
        url_hash=row["url_hash"],
        text_hash=row["text_hash"],
        published_at=row["published_at"],
        collected_at=row["collected_at"],
        status=row["status"],
        is_relevant=bool(row["is_relevant"]
                         ) if row["is_relevant"] is not None else None,
        relevance_reason=row["relevance_reason"],
        categories=categories,
        category_confidence=row["category_confidence"],
        is_whitelist=bool(row["is_whitelist"]),
    )
