"""Базовый класс коллектора."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List

log = logging.getLogger("collectors.base")


class BaseCollector(ABC):
    """Базовый класс для всех коллекторов."""

    def __init__(self, source_config: Dict):
        self.name = source_config.get("name", "unknown")
        self.url = source_config.get("url", "")
        self.is_whitelist = source_config.get("whitelist", False)
        self.config = source_config

    @abstractmethod
    async def collect(self) -> List[Dict]:
        """Собирает статьи. Возвращает список словарей:
        {source_name, source_type, title, text, url, published_at, is_whitelist}
        """
        pass

    def _normalize_item(
        self,
        title: str,
        text: str,
        url: str,
        published_at: datetime = None,
    ) -> Dict:
        return {
            "source_name": self.name,
            "source_type": self.config.get("type", "unknown"),
            "title": title.strip()[:500],
            "text": text.strip()[:10000],
            "url": url.strip(),
            "published_at": published_at or datetime.now(timezone.utc),
            "is_whitelist": self.is_whitelist,
        }
