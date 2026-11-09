"""Сборка дайджеста — объединение саммари в единый пост."""
from datetime import datetime

from config.settings import settings


def assemble_digest(issue_number: int, summaries: dict) -> str:
    """Собирает полный дайджест из саммари по категориям.

    Args:
        issue_number: номер выпуска (оставлен для совместимости, но в тексте не используется)
        summaries: {category: summary_text}

    Returns:
        Готовый текст дайджеста
    """
    today = datetime.now().strftime("%d.%m.%Y")

    lines = []
    
    lines.append(f"📰 Дайджест /Solidus | {today}")
    lines.append("")
    
    for cat in settings.CATEGORIES:
        label = settings.CATEGORY_LABELS.get(cat, cat)
        summary = summaries.get(cat, "Нет значимых новостей в этой категории.")

        if not summary or "Нет значимых новостей" in summary:
            continue
            
        lines.append(f"📌 {label}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("────────────────────────────────────────")
        lines.append("")

    if lines and lines[-2] == "────────────────────────────────────────":
        lines.pop(-2)
        lines.pop(-1)

    # 4. Добавляем подпись в конце
    lines.append("")
    lines.append("Будьте в курсе с дайджестом от Solidus (https://t.me/SOLIDUS_business_club)")
    lines.append("/")

    return "\n".join(lines)
