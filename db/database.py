"""Инициализация SQLite базы данных."""
import logging

import aiosqlite

from config.settings import settings

log = logging.getLogger("db.database")

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    url_hash TEXT NOT NULL,
    text_hash TEXT,
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'new',
    is_relevant INTEGER,
    relevance_reason TEXT,
    categories TEXT,
    category_confidence REAL,
    is_whitelist INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    admin_decision TEXT,
    final_text TEXT,
    published_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);
CREATE INDEX IF NOT EXISTS idx_articles_text_hash ON articles(text_hash);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
"""


async def get_db():
    """Возвращает асинхронное соединение с БД."""
    db = await aiosqlite.connect(settings.DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


def init_db():
    """Синхронная инициализация БД (вызывается при старте)."""
    import sqlite3
    conn = sqlite3.connect(settings.DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    log.info("БД инициализирована: %s", settings.DB_PATH)
