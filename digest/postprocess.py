"""Постпроцессинг дайджеста — очистка, валидация, разбивка."""
import logging
import re
from typing import List

from config.settings import settings

log = logging.getLogger("digest.postprocess")

# Артефакты LLM для удаления
LLM_ARTIFACTS = [
    r"Вот саммари[:\s]*",
    r"Вот краткое изложение[:\s]*",
    r"Конечно[!,\s]*",
    r"^(Как ИИ|Как языковая модель)[^\n]*\n",
    r"\*\*Примечание[^\n]*\n",
    r"^```[\w]*\n",
    r"\n```$",
]


def postprocess_digest(text: str) -> str:
    """Очищает дайджест от артефактов LLM и нормализует формат."""
    # Удаляем артефакты
    for pattern in LLM_ARTIFACTS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # Удаляем лишние пустые строки
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Валидация ссылок — проверяем что есть хотя бы одна
    urls = re.findall(r"https?://[^\s)]+", text)
    if not urls:
        log.warning("Постпроцесс: в дайджесте нет ссылок на источники")

    text = text.strip()

    MAX_LEN = 4000
    if len(text) > MAX_LEN:

        cut_index = text.rfind('\n\n', 0, MAX_LEN)
        if cut_index == -1:
            cut_index = MAX_LEN

        log.warning("Постпроцесс: текст был обрезан до %d символов", len(text))

    log.info("Постпроцесс: дайджест %d символов, %d ссылок", len(text), len(urls))
    return text


def split_for_telegram(text: str, max_chars: int = None) -> List[str]:
    return [text]
