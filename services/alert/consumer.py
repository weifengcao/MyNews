"""Alert service that pushes breaking news to eligible subscribers."""
import logging

from common import config
from common.database import get_db_session
from common.kafka import create_kafka_consumer, create_kafka_producer
from database.models import Subscription

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def _match_subscribers(article):
    """Find subscribers interested in the article's tags for breaking alerts."""
    tags = set(article.get("category_tags", []))
    with get_db_session() as session:
        subs = (
            session.query(Subscription)
            .filter(Subscription.breaking_news_enabled.is_(True))
            .all()
        )

    if not tags:
        return subs

    matched = []
    for sub in subs:
        selected_topics = set(sub.selected_topics or [])
        if not selected_topics or selected_topics.intersection(tags):
            matched.append(sub)
    return matched


def run_alert_loop():
    """Consume cleaned articles and push breaking alerts immediately."""
    consumer = create_kafka_consumer(config.CLEANED_NEWS_TOPIC, "alert-service")
    producer = create_kafka_producer()

    if not consumer or not producer:
        logging.critical("Alert service cannot start without Kafka connectivity.")
        return

    logging.info("Alert service listening for breaking news on %s", config.CLEANED_NEWS_TOPIC)
    for message in consumer:
        article = message.value
        if not article.get("is_breaking_news"):
            continue

        subscribers = _match_subscribers(article)
        for sub in subscribers:
            payload = {
                "user_id": sub.user_id,
                "articles": [article],
                "priority": "high",
            }
            producer.send(config.DELIVERY_QUEUE_TOPIC, value=payload)
            logging.info("Queued breaking alert for %s", sub.user_id)
        producer.flush()


if __name__ == "__main__":
    run_alert_loop()
