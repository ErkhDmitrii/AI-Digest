"""Web-парсер — собирает статьи с сайтов без RSS."""
import logging
from typing import Dict, List

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

from collectors.base import BaseCollector

log = logging.getLogger("collectors.web")


class WebParser(BaseCollector):
    """Веб-парсер для сайтов без RSS."""

    async def collect(self) -> List[Dict]:
        articles: List[Dict] = []
        parser_type = self.config.get("parser", "generic")

        try:
            log.info("Web: парсинг %s (%s)", self.name, self.url)

            # Реалистичные заголовки, чтобы сайт думал, что зашел реальный человек
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            }

            # curl_cffi имитирует отпечаток браузера Chrome 124
            response = curl_requests.get(
                self.url, 
                headers=headers, 
                impersonate="chrome124", 
                timeout=30
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Маршрутизация: вызываем нужный парсер в зависимости от настроек в sources.yaml
            if parser_type == "matsne":
                articles = self._parse_matsne(soup)
            elif parser_type == "commersant":
                articles = self._parse_commersant(soup)
            elif parser_type == "bm_ge":
                articles = self._parse_bm_ge(soup)
            elif parser_type == "rs_ge":
                articles = self._parse_rs_ge(soup)
            elif parser_type == "justadvisors":
                articles = self._parse_justadvisors(soup)
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

    def _parse_commersant(self, soup: BeautifulSoup) -> List[Dict]:
        """Универсальный парсер для commersant.ge."""
        articles: List[Dict] = []
        seen: set[str] = set()
        
        for a_tag in soup.find_all("a", href=True):
            url = self._absolutize(a_tag["href"])
            
            if any(x in url for x in ["facebook.com", "twitter.com", "linkedin.com", "/tag/", "#", "javascript:"]):
                continue
                
            title_tag = a_tag.find(["h1", "h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
            
            if not title or len(title) < 20 or url in seen:
                continue
                
            seen.add(url)
            parent = a_tag.find_parent(["article", "div"])
            text = parent.get_text(separator=" ", strip=True) if parent else title
            
            articles.append(self._normalize_item(title, text[:1500], url))
            
        return articles[:15]


    def _parse_rs_ge(self, soup: BeautifulSoup) -> List[Dict]:
        """Универсальный парсер для rs.ge (Revenue Service)."""
        articles: List[Dict] = []
        seen: set[str] = set()
        
        for a_tag in soup.find_all("a", href=True):
            url = self._absolutize(a_tag["href"])

            # Отсеиваем мусор
            if any(x in url for x in ["facebook.com", "twitter.com", "/tag/", "javascript:", "mailto:"]):
                continue

            if url.endswith("#") or url.rstrip("/") in ["https://rs.ge/Home-en", "https://rs.ge"]:
                continue
                
            title_tag = a_tag.find(["h1", "h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)
            
            if not title or len(title) < 15 or url in seen:
                continue
                
            seen.add(url)
            parent = a_tag.find_parent(["article", "div", "li"])
            text = parent.get_text(separator=" ", strip=True) if parent else title
            
            articles.append(self._normalize_item(title, text[:1500], url))
            
        return articles[:15]


    def _parse_matsne(self, soup: BeautifulSoup) -> List[Dict]:
        """Парсер для matsne.gov.ge (оставлен на всякий случай)."""
        articles: List[Dict] = []
        seen: set[str] = set()
        for item in soup.select("div.views-slideshow-cycle-main-frame-row-item"):
            link_tag = item.select_one(".views-field-title a[href]")
            if not link_tag: continue
            title = link_tag.get_text(strip=True)
            url = self._absolutize(link_tag.get("href", ""))
            if not url or url in seen: continue
            seen.add(url)
            text = item.get_text(separator=" ", strip=True)
            articles.append(self._normalize_item(title, text[:1500], url))
        return articles[:20]

    def _parse_generic(self, soup: BeautifulSoup) -> List[Dict]:
        """Универсальный парсер (запасной)."""
        articles: List[Dict] = []
        seen: set[str] = set()
        selectors = (
            "article, .post, .news-item, .article-card, "
            "div.views-row, div[class*='news'] div[class*='item']"
        )
        for item in soup.select(selectors)[:15]:
            title_tag = item.select_one("h1, h2, h3, .title, a[href]")
            link_tag = item.select_one("a[href]")
            if not title_tag or not link_tag: continue
            title = title_tag.get_text(strip=True)
            url = self._absolutize(link_tag.get("href", ""))
            if not url or url in seen: continue
            seen.add(url)
            text = item.get_text(separator=" ", strip=True)
            articles.append(self._normalize_item(title, text[:1500], url))
        return articles