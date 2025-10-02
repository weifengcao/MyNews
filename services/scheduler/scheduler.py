"""Scheduler service that produces digest tasks for due subscriptions."""
import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from common import config
from common.database import get_db_session
from common.kafka import create_kafka_producer
from database.models import Subscription

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def schedule_digests():
    """Query due subscriptions and produce digest tasks to Kafka."""
    producer = create_kafka_producer()
    if not producer:
        logging.error("Cannot run schedule job without a Kafka producer.")
        return

    with get_db_session() as db_session:
        logging.info("Checking for due subscriptions...")
        due_subscriptions = (
            db_session.query(Subscription)
            .filter(Subscription.delivery_schedule == "daily")
            .all()
        )

        for sub in due_subscriptions:
            task = {
                "subscription_id": sub.id,
                "user_id": sub.user_id,
                "time_window_start": time.time() - 86400,
                "priority": "low",
            }
            producer.send(config.DIGEST_TASKS_TOPIC, value=task)
            logging.info("Produced digest task for user %s", sub.user_id)

        producer.flush()


def run_scheduler(interval_seconds: int = 60):
    """Start the blocking scheduler loop."""
    scheduler = BlockingScheduler()
    scheduler.add_job(schedule_digests, "interval", seconds=interval_seconds)
    logging.info("Scheduler started. Press Ctrl+C to exit.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):  # pragma: no cover - CLI flow
        logging.info("Scheduler shutting down.")


if __name__ == "__main__":
    run_scheduler()
