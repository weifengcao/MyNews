"""Enrichment service that tags incoming articles and routes them for storage/alerts."""
import logging
from typing import Dict, List

from common import config
from common.kafka import create_kafka_consumer, create_kafka_producer

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def _categorize(article: Dict) -> List[str]:
    """Lightweight keyword-based categorization for demo purposes."""
    keywords = {
        "tech": ("technology", "software", "startup", "ai", "quantum"),
        "science": ("research", "space", "physics", "biology"),
        "business": ("market", "finance", "earnings", "economy"),
        "security": ("vulnerability", "breach", "malware", "ransomware"),
    }
    summary = (article.get("summary") or "").lower()
    title = (article.get("title") or "").lower()
    combined = f"{title} {summary}"

    found = {
        topic
        for topic, cues in keywords.items()
        if any(cue in combined for cue in cues)
    }
    return sorted(found)


def _is_breaking(article: Dict) -> bool:
    """Flag breaking news based on heuristic keywords."""
    headline = (article.get("title") or "").lower()
    return any(term in headline for term in ("breaking", "urgent", "just in"))


def run_enrichment_loop():
    """Consume raw news, enrich with metadata, and publish clean articles."""
    consumer = create_kafka_consumer(config.RAW_NEWS_TOPIC, "enrichment-service")
    producer = create_kafka_producer()

    if not consumer or not producer:
        logging.critical("Enrichment service cannot start without Kafka connectivity.")
        return

    logging.info("Enrichment service consuming from %s", config.RAW_NEWS_TOPIC)
    for message in consumer:
        article = message.value
        enriched = {
            **article,
            "category_tags": _categorize(article),
            "is_breaking_news": _is_breaking(article),
        }
        producer.send(config.CLEANED_NEWS_TOPIC, value=enriched)
        logging.info("Enriched article forwarded: %s", article.get("title"))
        producer.flush()


if __name__ == "__main__":
    run_enrichment_loop()
