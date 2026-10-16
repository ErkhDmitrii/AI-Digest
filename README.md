# AI-Дайджест — микросервис сбора и публикации новостей

Микросервис для автоматического сбора, фильтрации, саммаризации и публикации 
дайджеста новостей Грузии (законы, банки, рынок Батуми) в Telegram-канал.

## Архитектура

```
collectors (RSS/TG/Web) → DB (SQLite) → prefilter → dedup
    → LLM classifier → LLM categorizer → LLM summarizer
    → assembler → postprocess → bot (draft → admin approve → publish)
```

## Установка

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Linux:  source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # заполнить токены
python main.py
```

## Источники

- RSS: Парламент Грузии, Нацбанк, Таможня, Business Georgia, TABK
- Telegram: каналы о бизнесе и законодательстве Грузии


## Команды

- `python main.py` — запуск сервиса
- `python calibrate.py sample.csv` — калибровка промптов
