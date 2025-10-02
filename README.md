# MyNews

A Personalized News Aggregation and Delivery System using Kafka and lightweight NLP enrichment.

## Project Overview

This proof-of-concept demonstrates how MyNews ingests a continuous firehose of articles, enriches them, and delivers personalized digests:
1. Fetch articles from RSS feeds and publish them to Kafka.
2. Enrich the articles with simple metadata and flag breaking news.
3. Persist enriched articles to Elasticsearch for fast retrieval.
4. Trigger digest creation on a schedule and assemble personalized bundles.
5. Deliver digests and high-priority alerts to subscribers.

## Service Topology

The codebase is organized around two parallel paths called out in `DESIGN.md`:

- **Path 1 – Ingestion & Enrichment**
  - `services/ingestion/producer.py`: RSS fetcher that writes raw articles to `raw_news_topic`.
  - `services/enrichment/consumer.py`: Adds category tags / breaking flag and forwards to `cleaned_news_topic`.
  - `services/storage/consumer.py`: Persists enriched articles into Elasticsearch.

- **Path 2 – Subscription & Delivery**
  - `services/scheduler/scheduler.py`: Emits digest tasks to `digest_tasks_topic` based on schedules stored in Postgres.
  - `services/aggregation/consumer.py`: Reads tasks, pulls subscription filters, queries Elasticsearch, and stages digests on `delivery_queue_topic`.
  - `services/alert/consumer.py`: Listens for breaking news and immediately stages high-priority alerts on the same delivery queue.
  - `services/delivery/consumer.py`: Simulates email/push delivery and updates `last_digest_sent_at` in Postgres.

- **API**
  - `api/main.py`: FastAPI application for managing subscription preferences.

Support utilities live under `common/` (configuration, Kafka/DB helpers), `database/` (SQLAlchemy models), and `tools/` (index bootstrapper, topic logger).

## Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose

### Bootstrapping the Infrastructure

1. **Start Kafka, Zookeeper, PostgreSQL, and Elasticsearch**
   ```bash
   docker-compose up -d
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Seed PostgreSQL with demo subscriptions**
   ```bash
   python seed_db.py
   ```

4. **Create the Elasticsearch index**
   ```bash
   python tools/setup_es_index.py
   ```

### Running the Services

Start each service in its own terminal (or process manager):
```bash
python services/ingestion/producer.py
python services/enrichment/consumer.py
python services/storage/consumer.py
python services/scheduler/scheduler.py
python services/aggregation/consumer.py
python services/alert/consumer.py
python services/delivery/consumer.py
```

Run the API with Uvicorn:
```bash
uvicorn api.main:app --reload
```
Visit `http://localhost:8000/docs` for interactive documentation. Example request to disable breaking news for `user_1`:
```bash
curl -X PUT "http://localhost:8000/subscriptions/user_1" \
  -H "Content-Type: application/json" \
  -d '{"breaking_news_enabled": false}'
```

### Developer Utilities

- **Topic logger**: `python tools/log_consumer.py delivery_queue_topic`
- **Elasticsearch index bootstrap**: `python tools/setup_es_index.py`

Both utilities rely on the shared configuration in `common/config.py`.
