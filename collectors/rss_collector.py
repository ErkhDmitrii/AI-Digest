"""RSS-коллектор — собирает статьи из RSS-лент."""
import logging
from datetime import datetime, timezone
from typing import Dict, List

import feedparser

from collectors.base import BaseCollector

log = logging.getLogger("collectors.rss")


class RSSCollector(BaseCollector):
    """Коллектор RSS-фидов."""

    async def collect(self) -> List[Dict]:
        articles = []
        try:
            log.info("RSS: сбор из %s (%s)", self.name, self.url)
            feed = feedparser.parse(self.url)

            if feed.bozo and not feed.entries:
                log.warning("RSS: ошибка парсинга %s: %s",
                            self.name, feed.bozo_exception)
                return articles

            for entry in feed.entries[:20]:  # максимум 20 за раз
                title = entry.get("title", "")
                url = entry.get("link", "")
                text = entry.get("summary", "") or entry.get("description", "")

                published_at = datetime.now(timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_at = datetime(
                            *entry.published_parsed[:6], tzinfo=timezone.utc)
                    except Exception:
                        pass

                if title and url and text:
                    articles.append(self._normalize_item(
                        title, text, url, published_at))

            log.info("RSS: собрано %d статей из %s", len(articles), self.name)

        except Exception as e:
            log.error("RSS: ошибка сбора %s: %s", self.name, e)

        return articles
