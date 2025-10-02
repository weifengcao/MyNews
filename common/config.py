"""Central configuration values used across services."""

# Kafka Configuration
KAFKA_BROKER = "localhost:9092"
RAW_NEWS_TOPIC = "raw_news_topic"
CLEANED_NEWS_TOPIC = "cleaned_news_topic"
DIGEST_TASKS_TOPIC = "digest_tasks_topic"
DELIVERY_QUEUE_TOPIC = "delivery_queue_topic"

# Database Configuration
DATABASE_URL = "postgresql://user:password@localhost:5432/mynews"

# Elasticsearch Configuration
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ES_INDEX_NAME = "news_articles"

# Logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
