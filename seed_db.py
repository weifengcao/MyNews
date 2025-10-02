"""Initialize PostgreSQL schema and seed demo subscriptions."""
import logging

from common import config
from common.database import get_engine, get_session_factory
from database.models import Base, Subscription

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def seed_data():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logging.info("Tables created.")

    SessionLocal = get_session_factory()
    db = SessionLocal()

    if db.query(Subscription).count() > 0:
        logging.info("Database already seeded.")
        db.close()
        return

    subscriptions = [
        Subscription(
            user_id="user_1",
            selected_topics=["tech", "science"],
            delivery_schedule="daily",
            breaking_news_enabled=True,
        ),
        Subscription(
            user_id="user_2",
            selected_topics=["business"],
            delivery_schedule="daily",
            breaking_news_enabled=False,
        ),
        Subscription(
            user_id="user_3",
            selected_sources=["http://www.techmeme.com/feed.xml"],
            delivery_schedule="weekly",
        ),
    ]
    db.add_all(subscriptions)
    db.commit()
    logging.info("Added %s sample subscriptions.", len(subscriptions))
    db.close()


if __name__ == "__main__":
    seed_data()
