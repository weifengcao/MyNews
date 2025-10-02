"""RSS ingestion service that publishes raw articles to Kafka."""
import logging
import time
from typing import Iterable

import feedparser

from common import config
from common.kafka import create_kafka_producer

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)

DEFAULT_RSS_FEEDS: Iterable[str] = (
    "http://feeds.arstechnica.com/arstechnica/index",
    "https://www.wired.com/feed/category/science/latest",
    "http://www.techmeme.com/feed.xml",
)


def fetch_and_produce_news(producer, feed_url: str) -> None:
    """Fetch news entries from a feed URL and publish them to Kafka."""
    feed = feedparser.parse(feed_url)
    logging.info("Fetched %s entries from %s", len(feed.entries), feed_url)

    for entry in feed.entries:
        article = {
            "source_url": feed_url,
            "title": entry.title,
            "link": entry.link,
            "published_at": entry.get("published", ""),
            "summary": entry.summary,
        }
        producer.send(
            config.RAW_NEWS_TOPIC,
            value=article,
            key=article["link"].encode("utf-8"),
        )
        logging.info("Produced article: %s", article["title"])

    producer.flush()


def run_ingestion_loop(feeds: Iterable[str] = DEFAULT_RSS_FEEDS, interval_seconds: int = 900) -> None:
    """Continuously cycle through feeds and publish new articles."""
    producer = create_kafka_producer()
    if not producer:
        logging.critical("Cannot start ingestion without Kafka connectivity.")
        return

    while True:
        for feed in feeds:
            fetch_and_produce_news(producer, feed)
        logging.info("Completed feed cycle. Sleeping for %s seconds.", interval_seconds)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_ingestion_loop()
