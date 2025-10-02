"""Create Elasticsearch index with appropriate mapping for articles."""
import logging

from common import config
from common.search import create_es_client

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


MAPPING = {
    "properties": {
        "title": {"type": "text"},
        "summary": {"type": "text"},
        "category_tags": {"type": "keyword"},
        "published_at": {"type": "date", "format": "yyyy-MM-dd'T'HH:mm:ss||strict_date_optional_time"},
        "is_breaking_news": {"type": "boolean"},
    }
}


def setup_index():
    es_client = create_es_client()
    if not es_client:
        return

    index_name = config.ES_INDEX_NAME
    if es_client.indices.exists(index=index_name):
        logging.info("Index '%s' already exists.", index_name)
        return

    es_client.indices.create(index=index_name, mappings=MAPPING)
    logging.info("Index '%s' created.", index_name)


if __name__ == "__main__":
    setup_index()
