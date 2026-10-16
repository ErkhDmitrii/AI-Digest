"""Калибровка промптов — тестирование на размеченной выборке.

Использование: python calibrate.py sample.csv

CSV формат: title,text,expected_relevant,expected_category
"""
import asyncio
import csv
import json
import logging
import sys
from pathlib import Path

from config.settings import settings
from db.models import Article
from llm.llm_client import LLMClient
from pipeline.filter import _categorize, _classify_relevance

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("calibrate")


def load_sample(filepath: str):
    """Загружает тестовую выборку из CSV."""
    samples = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append({
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "expected_relevant": row.get("expected_relevant", "true").lower() == "true",
                "expected_category": row.get("expected_category", ""),
            })
    return samples


async def calibrate(samples):
    """Запускает калибровку на выборке, считает precision/recall/F1."""
    client = LLMClient()

    tp = fp = fn = tn = 0
    cat_correct = cat_total = 0

    for i, sample in enumerate(samples):
        article = Article(
            title=sample["title"],
            text=sample["text"],
            source_name="calibration",
            source_type="test",
            is_whitelist=False,
        )

        # Классификация
        is_relevant, reason, conf = await _classify_relevance(client, article)

        # Сравнение с ожиданием
        expected = sample["expected_relevant"]
        if expected and is_relevant:
            tp += 1
        elif expected and not is_relevant:
            fn += 1
        elif not expected and is_relevant:
            fp += 1
        else:
            tn += 1

        # Категоризация (если релевантно)
        if is_relevant and sample["expected_category"]:
            categories, _ = await _categorize(client, article)
            if sample["expected_category"] in categories:
                cat_correct += 1
            cat_total += 1

        log.info(
            "[%d/%d] rel=%s (exp=%s) conf=%.2f reason=%s",
            i + 1, len(samples), is_relevant, expected, conf, reason[:50]
        )

    # Метрики
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / \
        (precision + recall) if (precision + recall) > 0 else 0
    cat_acc = cat_correct / cat_total if cat_total > 0 else 0

    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ КАЛИБРОВКИ")
    print("=" * 50)
    print(f"Всего образцов: {len(samples)}")
    print(f"TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"Precision: {precision:.2%}")
    print(f"Recall:    {recall:.2%}")
    print(f"F1:        {f1:.2%}")
    print(f"Категории (точность): {cat_acc:.2%} ({cat_correct}/{cat_total})")
    print("=" * 50)

    return {"precision": precision, "recall": recall, "f1": f1, "cat_accuracy": cat_acc}


def main():
    if len(sys.argv) < 2:
        print("Использование: python calibrate.py sample.csv")
        sys.exit(1)

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"Файл не найден: {filepath}")
        sys.exit(1)

    samples = load_sample(filepath)
    log.info("Загружено %d образцов", len(samples))
    asyncio.run(calibrate(samples))


if __name__ == "__main__":
    main()
