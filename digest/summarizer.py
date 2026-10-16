"""LLM-саммаризатор — сжимает статьи в блок дайджеста."""
import logging
from typing import List

from config.settings import settings
from db.models import Article
from llm.llm_client import LLMClient

log = logging.getLogger("digest.summarizer")


async def summarize_category(category: str, articles: List[Article]) -> str:
    """Саммаризация статей одной категории через LLM.

    Args:
        category: категория (laws, banking, market)
        articles: список статей этой категории

    Returns:
        Текст саммари для блока дайджеста
    """
    if not articles:
        return "Нет значимых новостей в этой категории."

    # Ограничиваем количество статей
    articles = articles[:settings.MAX_ITEMS_PER_CATEGORY]

    prompt = settings.prompts.get("summarizer_v1", "")
    category_label = settings.CATEGORY_LABELS.get(category, category)

    # Формируем входной текст со статьями
    articles_text = ""
    for i, art in enumerate(articles, 1):
        articles_text += (
            f"Статья {i}:\n"
            f"Источник: {art.source_name}\n"
            f"Заголовок: {art.title}\n"
            f"Текст: {art.text[:1500]}\n"
            f"URL: {art.url}\n\n"
        )

    user_msg = (
        f"Категория: {category_label}\n"
        f"Количество статей: {len(articles)}\n\n"
        f"{articles_text}"
    )

    try:
        client = LLMClient()
        summary = await client.chat(prompt, user_msg)
        log.info("Саммари для категории '%s' готово (%d символов)",
                 category, len(summary))
        return summary
    except Exception as e:
        log.error("Ошибка саммаризации категории '%s': %s", category, e)
        return f"Ошибка при создании саммари для категории '{category_label}'."
