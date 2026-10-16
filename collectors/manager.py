"""Менеджер коллекторов — оркестрирует сбор данных из всех источников."""
import asyncio
import logging
from pathlib import Path
from typing import Dict, List

import yaml

from collectors.rss_collector import RSSCollector
from collectors.telegram_collector import TelegramCollector
from collectors.web import WebParser
from config.settings import settings
from db.repository import save_article
from pipeline.dedup import compute_text_hash, is_duplicate_text
from pipeline.prefilter import should_skip

log = logging.getLogger("collectors.manager")


def load_sources() -> List[Dict]:
    """Загружает конфигурацию источников из YAML."""
    sources_path = settings.PROJECT_ROOT / "config" / "sources.yaml"
    with open(sources_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def _create_collector(source: Dict):
    """Создает коллектор нужного типа."""
    stype = source.get("type")
    if stype == "rss":
        return RSSCollector(source)
    elif stype == "telegram":
        return TelegramCollector(source)
    elif stype == "web":
        return WebParser(source)
    else:
        log.warning("Неизвестный тип источника: %s", stype)
        return None


async def run_collectors_once():
    """Один цикл сбора из всех источников."""
    sources = load_sources()
    log.info("Запуск сбора из %d источников", len(sources))

    total_saved = 0
    total_skipped = 0

    for source in sources:
        collector = _create_collector(source)
        if not collector:
            continue

        try:
            items = await collector.collect()
            for item in items:
                # Предфильтр
                if should_skip(item["title"], item["text"]):
                    total_skipped += 1
                    continue

                # Дедупликация по тексту
                text_hash = compute_text_hash(item["text"])
                if await is_duplicate_text(text_hash):
                    total_skipped += 1
                    continue

                # Сохранение
                saved = await save_article(
                    source_name=item["source_name"],
                    source_type=item["source_type"],
                    title=item["title"],
                    text=item["text"],
                    url=item["url"],
                    published_at=item["published_at"],
                    is_whitelist=item["is_whitelist"],
                    text_hash=text_hash,
                )
                if saved:
                    total_saved += 1

        except Exception as e:
            log.error("Ошибка сбора из %s: %s", source.get("name", "?"), e)

    log.info("Сбор завершён: сохранено %d, пропущено %d",
             total_saved, total_skipped)
    return total_saved
