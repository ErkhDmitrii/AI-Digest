"""Сборка дайджеста — объединение саммари в единый пост."""
from datetime import datetime

from config.settings import settings


def assemble_digest(issue_number: int, summaries: dict) -> str:
    """Собирает полный дайджест из саммари по категориям.

    Args:
        issue_number: номер выпуска
        summaries: {category: summary_text}

    Returns:
        Готовый текст дайджеста
    """
    today = datetime.now().strftime("%d.%m.%Y")

    lines = []
    lines.append(f"📋 AI-Дайджест Грузия | Выпуск #{issue_number} | {today}")
    lines.append("")
    lines.append("В этом выпуске:")
    for cat in settings.CATEGORIES:
        label = settings.CATEGORY_LABELS.get(cat, cat)
        lines.append(f"  • {label}")
    lines.append("")
    lines.append("─" * 40)
    lines.append("")

    for cat in settings.CATEGORIES:
        label = settings.CATEGORY_LABELS.get(cat, cat)
        summary = summaries.get(cat, "Нет значимых новостей в этой категории.")
        lines.append(f"📌 {label}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("─" * 40)
        lines.append("")

    lines.append("")

    return "\n".join(lines)
