"""Telegram-коллектор — собирает посты из каналов через Telethon."""
import logging
from datetime import datetime, timezone
from typing import Dict, List

from collectors.base import BaseCollector

log = logging.getLogger("collectors.tg")

# Глобальный клиент Telethon (создаётся один раз)
_tg_client = None
_tg_init_done = False


async def _get_tg_client():
    """Создаёт и возвращает Telethon-клиент (singleton)."""
    global _tg_client, _tg_init_done
    if _tg_client and _tg_init_done:
        return _tg_client

    from telethon import TelegramClient

    from config.settings import settings

    if not settings.TELETHON_API_ID or not settings.TELETHON_API_HASH:
        log.error("Telethon: API_ID/API_HASH не настроены")
        return None

    _tg_client = TelegramClient(
        settings.TELETHON_SESSION,
        settings.TELETHON_API_ID,
        settings.TELETHON_API_HASH,
    )
    await _tg_client.start()
    _tg_init_done = True
    log.info("Telethon клиент запущен")
    return _tg_client


class TelegramCollector(BaseCollector):
    """Коллектор Telegram-каналов."""

    async def collect(self) -> List[Dict]:
        articles = []
        channel = self.config.get("channel", "")
        if not channel:
            log.warning("TG: не указан канал для %s", self.name)
            return articles

        try:
            client = await _get_tg_client()
            if not client:
                return articles

            log.info("TG: сбор из @%s", channel)
            entity = await client.get_entity(channel)
            messages = await client.get_messages(entity, limit=15)

            for msg in messages:
                if not msg or not msg.text:
                    continue

                title = msg.text[:200].replace("\n", " ")
                url = f"https://t.me/{channel}/{msg.id}"
                published_at = msg.date if msg.date else datetime.now(
                    timezone.utc)

                articles.append(self._normalize_item(
                    title, msg.text, url, published_at))

            log.info("TG: собрано %d постов из @%s", len(articles), channel)

        except Exception as e:
            log.error("TG: ошибка сбора @%s: %s", channel, e)

        return articles
