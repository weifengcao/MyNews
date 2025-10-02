"""Helpers for interacting with Elasticsearch."""
import logging
import time
from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError

from common import config


def create_es_client(max_retries: int = 5, retry_sleep: int = 5) -> Optional[Elasticsearch]:
    """Create an Elasticsearch client with retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            es_client = Elasticsearch(
                [
                    {
                        "host": config.ELASTICSEARCH_HOST,
                        "port": config.ELASTICSEARCH_PORT,
                        "scheme": "http",
                    }
                ]
            )
            if es_client.ping():
                logging.info("Elasticsearch connection established.")
                return es_client
        except ESConnectionError:
            logging.warning(
                "Failed to connect to Elasticsearch. Retry %s/%s in %s seconds.",
                attempt,
                max_retries,
                retry_sleep,
            )
            time.sleep(retry_sleep)
    logging.error("Unable to connect to Elasticsearch after %s attempts.", max_retries)
    return None
