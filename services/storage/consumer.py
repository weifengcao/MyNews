"""Storage service that persists enriched articles into Elasticsearch."""
import logging
from typing import Dict

from common import config
from common.kafka import create_kafka_consumer
from common.search import create_es_client

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def _index_article(es_client, article: Dict) -> None:
    """Index an article into Elasticsearch."""
    article_id = article.get("link") or article.get("title")
    if not article_id:
        logging.warning("Skipping article without identifier: %s", article)
        return

    es_client.index(index=config.ES_INDEX_NAME, id=article_id, document=article)
    logging.info("Indexed article %s into %s", article_id, config.ES_INDEX_NAME)


def run_storage_loop():
    """Consume cleaned articles and write them into Elasticsearch."""
    consumer = create_kafka_consumer(config.CLEANED_NEWS_TOPIC, "storage-service")
    es_client = create_es_client()

    if not consumer or not es_client:
        logging.critical("Storage service cannot start without Kafka and Elasticsearch.")
        return

    logging.info("Storage service consuming from %s", config.CLEANED_NEWS_TOPIC)
    for message in consumer:
        _index_article(es_client, message.value)


if __name__ == "__main__":
    run_storage_loop()
