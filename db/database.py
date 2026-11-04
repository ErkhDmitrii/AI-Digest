"""Инициализация базы данных PostgreSQL."""
import logging

import asyncpg

from config.settings import settings

log = logging.getLogger("db.database")

# Глобальный пул соединений
pool: asyncpg.Pool = None

async def init_db():
    """Создает пул соединений и инициализирует таблицы."""
    global pool
    log.info("Подключение к PostgreSQL %s:%s/%s...", settings.DB_HOST, settings.DB_PORT, settings.DB_NAME)
    
    pool = await asyncpg.create_pool(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        min_size=2,
        max_size=10
    )

    async with pool.acquire() as conn:
        # Таблица статей
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                source_name VARCHAR(255),
                source_type VARCHAR(50),
                title TEXT,
                text TEXT,
                url TEXT UNIQUE,
                url_hash VARCHAR(64) UNIQUE,
                text_hash VARCHAR(64),
                published_at TIMESTAMP,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50) DEFAULT 'new',
                is_relevant BOOLEAN,
                relevance_reason TEXT,
                categories JSONB,
                category_confidence DOUBLE PRECISION,
                is_whitelist BOOLEAN DEFAULT FALSE
            );
        ''')
        
        # Таблица дайджестов
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS digests (
                id SERIAL PRIMARY KEY,
                issue_number INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content TEXT,
                status VARCHAR(50) DEFAULT 'draft',
                admin_decision VARCHAR(50),
                final_text TEXT,
                published_at TIMESTAMP
            );
        ''')
    log.info("База данных PostgreSQL инициализирована.")
