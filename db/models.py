"""Dataclass-модели данных."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Article:
    id: Optional[int] = None
    source_name: str = ""
    source_type: str = ""
    title: str = ""
    text: str = ""
    url: str = ""
    url_hash: str = ""
    text_hash: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    status: str = "new"
    is_relevant: Optional[bool] = None
    relevance_reason: Optional[str] = None
    categories: Optional[List[str]] = None
    category_confidence: Optional[float] = None
    is_whitelist: bool = False


@dataclass
class Digest:
    id: Optional[int] = None
    issue_number: int = 0
    created_at: Optional[datetime] = None
    content: str = ""
    status: str = "draft"
    admin_decision: Optional[str] = None
    final_text: Optional[str] = None
    published_at: Optional[datetime] = None
