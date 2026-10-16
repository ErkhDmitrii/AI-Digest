"""LLM-фильтрация и категоризация статей."""
import json
import logging
from typing import List, Tuple

from config.settings import settings
from db.models import Article
from db.repository import get_unfiltered_articles, update_article_filter
from llm.llm_client import LLMClient

log = logging.getLogger("pipeline.filter")


async def filter_and_categorize() -> dict:
    """Фильтрует и категоризует новые статьи через LLM.
    Возвращает статистику: {total, relevant, filtered_out}.
    """
    client = LLMClient()
    articles = await get_unfiltered_articles()
    log.info("Фильтрация: %d новых статей", len(articles))

    stats = {"total": len(articles), "relevant": 0, "filtered_out": 0}

    for article in articles:
        try:
            # Классификация релевантности
            is_relevant, reason, confidence = await _classify_relevance(client, article)

            # Категоризация (только если релевантно)
            categories = []
            cat_confidence = 0.0
            if is_relevant:
                categories, cat_confidence = await _categorize(client, article)
                stats["relevant"] += 1
            else:
                stats["filtered_out"] += 1

            await update_article_filter(
                article.id, is_relevant, reason, categories, cat_confidence
            )

            log.debug(
                "Статья %d: relevant=%s, cats=%s, reason=%s",
                article.id, is_relevant, categories, reason
            )

        except Exception as e:
            log.error("Ошибка фильтрации статьи %d: %s", article.id, e)
            # Отмечаем как отфильтрованную с ошибкой
            await update_article_filter(article.id, False, f"LLM error: {e}")

    log.info(
        "Фильтрация завершена: relevant=%d, filtered_out=%d",
        stats["relevant"], stats["filtered_out"]
    )
    return stats


async def _classify_relevance(client: LLMClient, article: Article) -> Tuple[bool, str, float]:
    """Классифицирует релевантность статьи через LLM."""
    prompt = settings.prompts.get("classifier_v1", "")

    # Whitelist-логика: пониженный порог
    threshold = 0.3 if article.is_whitelist else 0.6

    user_msg = (
        f"Источник: {article.source_name} (whitelist: {article.is_whitelist})\n"
        f"Заголовок: {article.title}\n"
        f"Текст: {article.text[:2000]}"
    )

    try:
        result = await client.chat_json(prompt, user_msg)
        is_relevant = result.get("relevant", False)
        confidence = float(result.get("confidence", 0.0))
        reason = result.get("reason", "")

        # Применяем порог
        if is_relevant and confidence < threshold:
            is_relevant = False
            reason = f"Порог {threshold} не пройден (conf={confidence}): {reason}"

        return is_relevant, reason, confidence

    except Exception as e:
        log.error("LLM classify error: %s", e)
        return False, f"LLM error: {e}", 0.0


async def _categorize(client: LLMClient, article: Article) -> Tuple[List[str], float]:
    """Категоризует статью через LLM."""
    prompt = settings.prompts.get("categorizer_v1", "")

    user_msg = (
        f"Заголовок: {article.title}\n"
        f"Текст: {article.text[:2000]}"
    )

    try:
        result = await client.chat_json(prompt, user_msg)
        categories = result.get("categories", [])
        confidence = float(result.get("confidence", 0.0))

        # Фильтруем только валидные категории
        categories = [c for c in categories if c in settings.CATEGORIES]

        return categories, confidence

    except Exception as e:
        log.error("LLM categorize error: %s", e)
        return [], 0.0
