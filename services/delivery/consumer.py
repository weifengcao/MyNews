"""Delivery service that simulates sending digests and updates delivery status."""
import logging
from datetime import datetime

from sqlalchemy import update

from common import config
from common.database import get_db_session
from common.kafka import create_kafka_consumer
from database.models import Subscription

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def _deliver_digest(payload):
    """Simulate delivery by logging articles and updating the database."""
    user_id = payload.get("user_id")
    articles = payload.get("articles", [])

    logging.info("Delivering digest to user: %s", user_id)
    for article in articles:
        logging.info("  - %s (%s)", article.get("title"), article.get("link"))

    stmt = (
        update(Subscription)
        .where(Subscription.user_id == user_id)
        .values(last_digest_sent_at=datetime.utcnow())
    )
    with get_db_session() as session:
        session.execute(stmt)
    logging.info("Updated last_digest_sent_at for user: %s", user_id)


def run_delivery_loop():
    """Consume delivery queue messages and process digests."""
    consumer = create_kafka_consumer(config.DELIVERY_QUEUE_TOPIC, "delivery-service")
    if not consumer:
        logging.critical("Delivery service cannot start without Kafka connectivity.")
        return

    logging.info("Delivery service consuming from %s", config.DELIVERY_QUEUE_TOPIC)
    for message in consumer:
        _deliver_digest(message.value)


if __name__ == "__main__":
    run_delivery_loop()
