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

    # Обрезаем лишнее в начале/конце
    text = text.strip()

    log.info("Постпроцесс: дайджест %d символов, %d ссылок",
             len(text), len(urls))
    return text


def split_for_telegram(text: str, max_chars: int = None) -> List[str]:
    """Разбивает текст на части для Telegram (лимит 4096 символов).

    Разбивка по пустым строкам, сохраняя заголовки.
    """
    if max_chars is None:
        max_chars = settings.MAX_TELEGRAM_CHARS

    if len(text) <= max_chars:
        return [text]

    parts = []
    current_part = ""
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current_part) + len(para) + 2 <= max_chars:
            current_part += para + "\n\n"
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = para + "\n\n"

    if current_part:
        parts.append(current_part.strip())

    # Добавляем номера частей
    if len(parts) > 1:
        parts = [f"(Часть {i+1}/{len(parts)})\n\n{p}" for i,
                 p in enumerate(parts)]

    log.info("Постпроцесс: разбит на %d частей", len(parts))
    return parts
