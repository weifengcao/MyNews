"""SQLAlchemy models for persistent entities."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, unique=True)
    selected_topics = Column(JSON)
    selected_sources = Column(JSON)
    delivery_schedule = Column(String, default="daily")
    breaking_news_enabled = Column(Boolean, default=False)
    last_digest_sent_at = Column(DateTime)

    def mark_delivered(self):
        self.last_digest_sent_at = datetime.utcnow()

    def __repr__(self):  # pragma: no cover - for debugging only
        return f"<Subscription user_id={self.user_id!r} schedule={self.delivery_schedule!r}>"
