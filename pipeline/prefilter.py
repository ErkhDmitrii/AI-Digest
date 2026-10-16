"""Хардкодный предфильтр — быстрая отбраковка по стоп-словам, длине и дате."""
import logging
from datetime import datetime, timezone

from config.settings import settings

log = logging.getLogger("pipeline.prefilter")

STOP_WORDS = [
    "реклама", "спонсор", "промо", "купить со скидкой",
    "казино", "ставки на спорт", "1xbet", "промокод",
    "подпишись", "подписка на канал", "перешли это",
]

MIN_LENGTH = 100  # минимальная длина текста


def should_skip(title: str, text: str, published_at: datetime = None) -> bool:
    """Возвращает True если статью нужно пропустить."""
    full_text = f"{title} {text}".lower()

    # Стоп-слова
    for word in STOP_WORDS:
        if word in full_text:
            log.debug("Предфильтр: стоп-слово '%s' в '%s'", word, title[:50])
            return True

    # Длина
    if len(text) < MIN_LENGTH:
        log.debug("Предфильтр: слишком короткий (%d симв): %s", len(text), title[:50])
        return True

    # Возраст
    if published_at:
        age_days = (datetime.now(timezone.utc) - published_at).days
        if age_days > settings.MAX_ARTICLE_AGE_DAYS:
            log.debug("Предфильтр: старая (%d дней): %s", age_days, title[:50])
            return True

    return False
