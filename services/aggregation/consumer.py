"""Aggregation service that builds personalized digests for users."""
import logging
from typing import Dict, List

from common import config
from common.database import get_db_session
from common.kafka import create_kafka_consumer, create_kafka_producer
from common.search import create_es_client
from database.models import Subscription

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def _build_es_query(subscription: Subscription) -> Dict:
    """Construct a simple Elasticsearch query based on the subscription."""
    filters: List[Dict] = []

    if subscription.selected_topics:
        filters.append({"terms": {"category_tags.keyword": subscription.selected_topics}})
    if subscription.selected_sources:
        filters.append({"terms": {"source_url.keyword": subscription.selected_sources}})

    query: Dict = {"bool": {}}
    if filters:
        query["bool"]["filter"] = filters
    else:
        query = {"match_all": {}}

    return query


def _fetch_articles(es_client, subscription: Subscription, size: int = 10) -> List[Dict]:
    """Execute an Elasticsearch search for the subscription."""
    query = _build_es_query(subscription)
    results = es_client.search(index=config.ES_INDEX_NAME, query=query, size=size)
    hits = results.get("hits", {}).get("hits", [])
    return [hit["_source"] for hit in hits]


def run_aggregation_loop():
    """Consume digest tasks, query data sources, and produce delivery payloads."""
    consumer = create_kafka_consumer(config.DIGEST_TASKS_TOPIC, "aggregation-service")
    producer = create_kafka_producer()
    es_client = create_es_client()

    if not consumer or not producer or not es_client:
        logging.critical("Aggregation service cannot start without dependencies.")
        return

    logging.info("Aggregation service consuming from %s", config.DIGEST_TASKS_TOPIC)
    for message in consumer:
        task = message.value
        subscription_id = task.get("subscription_id")
        if not subscription_id:
            logging.warning("Skipping task without subscription id: %s", task)
            continue

        with get_db_session() as db_session:
            subscription = db_session.get(Subscription, subscription_id)
            if not subscription:
                logging.warning("No subscription found for id %s", subscription_id)
                continue

            articles = _fetch_articles(es_client, subscription)
            payload = {
                "user_id": subscription.user_id,
                "articles": articles,
                "priority": task.get("priority", "low"),
            }
            producer.send(config.DELIVERY_QUEUE_TOPIC, value=payload)
            logging.info("Produced digest for user %s with %s articles", subscription.user_id, len(articles))
            producer.flush()


if __name__ == "__main__":
    run_aggregation_loop()
