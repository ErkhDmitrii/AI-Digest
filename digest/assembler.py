"""Сборка дайджеста — объединение саммари в единый пост."""
from datetime import datetime, timedelta
from config.settings import settings


def assemble_digest(issue_number: int, summaries: dict) -> str:
    """Собирает полный дайджест из саммари по категориям."""

    today = datetime.now()
    last_week = today - timedelta(days=7)
    
    if today.month == last_week.month:
        date_str = f"{last_week.strftime('%d')} - {today.strftime('%d.%m.%Y')}"
    else:
        date_str = f"{last_week.strftime('%d.%m')} - {today.strftime('%d.%m.%Y')}"

    lines = []
    
    lines.append(f"📰 Дайджест /Solidus | {date_str}")
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
    lines.append("Будьте в курсе с дайджестом от [Solidus](https://t.me/SOLIDUS_business_club)")

    return "\n".join(lines)
