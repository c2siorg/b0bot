from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional
import hashlib


class NormalizedArticle(BaseModel):
    """
    Unified article schema used across ingestion, retrieval, and agent pipeline.

    This ensures:
    - deterministic IDs (no duplication in Pinecone)
    - cross-source deduplication via content_hash
    - standardized structure for all ingestion sources
    """

    id: str
    title: str
    source: str
    source_type: str  # 'rss' | 'scraper' | future: 'reddit', 'nvd'
    credibility_tier: int  # 1 (high), 2 (medium), 3 (low)
    published_at: datetime
    content: str
    tags: List[str]
    content_hash: str
    cvss_score: Optional[float] = None

    # -----------------------------
    # VALIDATORS
    # -----------------------------
    @field_validator("credibility_tier")
    def validate_tier(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError("credibility_tier must be 1, 2, or 3")
        return v

    # -----------------------------
    # STATIC HELPERS
    # -----------------------------
    @staticmethod
    def generate_id(source_url: str) -> str:
        """Deterministic ID based on source URL"""
        return hashlib.md5(source_url.encode()).hexdigest()

    @staticmethod
    def compute_content_hash(title: str, content: str) -> str:
        """Hash for deduplication across sources"""
        combined = (title + content).encode()
        return hashlib.sha256(combined).hexdigest()

    # -----------------------------
    # FACTORY METHODS
    # -----------------------------
    @classmethod
    def from_scraper_dict(cls, data: dict):
        """Create article from existing scraper output"""
        source_url = data.get("url")

        return cls(
            id=cls.generate_id(source_url),
            title=data.get("title", ""),
            source=data.get("source", "unknown"),
            source_type="scraper",
            credibility_tier=2,
            published_at=data.get("published_at"),
            content=data.get("content", ""),
            tags=data.get("tags", []),
            content_hash=cls.compute_content_hash(
                data.get("title", ""), data.get("content", "")
            ),
            cvss_score=None,
        )

    @classmethod
    def from_rss_entry(cls, entry):
        """Create article from RSS feed entry"""
        source_url = entry.link

        return cls(
            id=cls.generate_id(source_url),
            title=entry.title,
            source=getattr(entry, "source", "unknown"),
            source_type="rss",
            credibility_tier=1,
            published_at=datetime(*entry.published_parsed[:6]),
            content=getattr(entry, "summary", ""),
            tags=[],
            content_hash=cls.compute_content_hash(
                entry.title, getattr(entry, "summary", "")
            ),
            cvss_score=None,
        )