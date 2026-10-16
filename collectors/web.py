"""Web-парсер — собирает статьи с сайтов без RSS."""
import logging
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from collectors.base import BaseCollector

log = logging.getLogger("collectors.web")


class WebParser(BaseCollector):
    """Веб-парсер для сайтов без RSS."""

    async def collect(self) -> List[Dict]:
        articles: List[Dict] = []
        parser_type = self.config.get("parser", "generic")

        try:
            log.info("Web: парсинг %s (%s)", self.name, self.url)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/122.0 Safari/537.36",
                "Accept-Language": "ka,en;q=0.8,ru;q=0.6",
            }
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()

            # Явно указываем кодировку, если сайт не отдаёт корректный charset
            if not response.encoding or response.encoding.lower() == "iso-8859-1":
                response.encoding = response.apparent_encoding or "utf-8"

            soup = BeautifulSoup(response.text, "lxml")

            if parser_type == "matsne":
                articles = self._parse_matsne(soup)
            else:
                articles = self._parse_generic(soup)

            log.info("Web: собрано %d статей из %s", len(articles), self.name)

        except Exception as e:
            log.error("Web: ошибка парсинга %s: %s", self.name, e)

        return articles

    # ------------------------------------------------------------------ helpers

    def _absolutize(self, url: str) -> str:
        """Приводит относительный URL к абсолютному."""
        if not url:
            return ""
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("//"):
            return "https:" + url
        base = self.url.rstrip("/")
        return base + ("/" if not url.startswith("/") else "") + url

    # ------------------------------------------------------------------ parsers

    def _parse_matsne(self, soup: BeautifulSoup) -> List[Dict]:
        """Парсер для matsne.gov.ge: новостной слайдер + сайдбар изменений."""
        articles: List[Dict] = []
        seen: set[str] = set()

        # 1) Новостные слайды (верхняя карусель)
        for item in soup.select("div.views-slideshow-cycle-main-frame-row-item"):
            link_tag = item.select_one(".views-field-title a[href]")
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            if not title or len(title) < 15:
                continue
            url = self._absolutize(link_tag.get("href", ""))
            if not url or url in seen:
                continue
            seen.add(url)

            body_tag = item.select_one(".views-field-body .field-content")
            text = body_tag.get_text(separator=" ", strip=True) if body_tag else title
            # Приклеиваем дату к тексту — пригодится фильтру
            date_tag = item.select_one(".views-field-created .field-content")
            if date_tag:
                text = f"[{date_tag.get_text(strip=True)}] {text}"

            articles.append(self._normalize_item(title, text, url))

        # 2) Сайдбар "ცვლილებების მაცნე" — изменения в законодательстве
        for li in soup.select("div.sidebar-content > ul > li"):
            link_tag = li.select_one("a[href*='/ka/document/view/']")
            if not link_tag:
                continue
            url = self._absolutize(link_tag["href"])
            if not url or url in seen:
                continue
            seen.add(url)

            title = link_tag.get_text(strip=True)
            # Если текст ссылки пустой — берём весь текст li как заголовок
            if not title:
                title = li.get_text(separator=" ", strip=True)
            title = title.strip()
            if len(title) < 20:
                continue

            text = li.get_text(separator=" ", strip=True)
            articles.append(self._normalize_item(title, text, url))

        return articles[:20]

    def _parse_generic(self, soup: BeautifulSoup) -> List[Dict]:
        """Универсальный парсер — ищет статьи по общим признакам + Drupal-views."""
        articles: List[Dict] = []
        seen: set[str] = set()

        selectors = (
            "article, .post, .news-item, .article-card, "
            "div.views-row, div.views-slideshow-cycle-main-frame-row-item, "
            "div[class*='news'] div[class*='item'], li[class*='news']"
        )

        for item in soup.select(selectors)[:15]:
            title_tag = item.select_one(
                "h1, h2, h3, .title, .card-title, "
                ".views-field-title a, .field-content a, a[href]"
            )
            link_tag = item.select_one("a[href]")
            if not title_tag or not link_tag:
                continue

            title = title_tag.get_text(strip=True)
            if not title or len(title) < 20:
                continue

            url = self._absolutize(link_tag.get("href", ""))
            if not url or url in seen:
                continue
            seen.add(url)

            text = item.get_text(separator=" ", strip=True)
            articles.append(self._normalize_item(title, text, url))

        return articles