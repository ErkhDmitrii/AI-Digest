"""Оркестратор пайплайна: сбор → фильтр → дайджест."""
import logging

from collectors.manager import run_collectors_once
from pipeline.filter import filter_and_categorize
from digest.summarizer import summarize_category
from digest.assembler import assemble_digest
from digest.postprocess import postprocess_digest
from db.repository import (
    get_articles_for_digest,
    mark_articles_used,
    save_digest,
    get_next_issue_number,
)

log = logging.getLogger("pipeline.orchestrator")


async def run_full_pipeline() -> str:
    """Полный цикл: сбор → фильтр → саммаризация → сборка → постпроцесс.
    Возвращает готовый текст дайджеста.
    """
    log.info("=== Запуск полного пайплайна ===")

    # 1. Сбор данных
    log.info("Шаг 1: Сбор данных")
    await run_collectors_once()

    # 2. Фильтрация и категоризация
    log.info("Шаг 2: Фильтрация и категоризация")
    stats = await filter_and_categorize()
    log.info("Статистика фильтрации: %s", stats)

    # 3. Получение статей для дайджеста
    log.info("Шаг 3: Подготовка статей для дайджеста")
    articles_by_cat = await get_articles_for_digest()

    # 4. Саммаризация по категориям
    log.info("Шаг 4: Саммаризация")
    summaries = {}
    for category, articles in articles_by_cat.items():
        if articles:
            summary = await summarize_category(category, articles)
            summaries[category] = summary
        else:
            summaries[category] = "Нет значимых новостей в этой категории."

    # 5. Сборка дайджеста
    log.info("Шаг 5: Сборка дайджеста")
    issue_number = await get_next_issue_number()
    raw_digest = assemble_digest(issue_number, summaries)

    # 6. Постпроцессинг
    log.info("Шаг 6: Постпроцессинг")
    final_text = postprocess_digest(raw_digest)

    # 7. Сохранение в БД
    log.info("Шаг 7: Сохранение черновика")
    await save_digest(issue_number, final_text)

    # 8. Отметка статей как использованных
    await mark_articles_used()

    log.info("=== Пайплайн завершён, выпуск #%d ===", issue_number)
    return final_text
