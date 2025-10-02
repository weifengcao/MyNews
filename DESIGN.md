# MyNews - System Design

This document outlines the architecture for the MyNews Personalized News Aggregation and Delivery System.

## 1. Core Goal and Parallel Paths 🎯

The system is designed around two highly decoupled, parallel paths to handle continuous data processing and personalized user delivery:

| Path                      | Primary Function                           | Data Flow                            | Key Operations                               |
| ------------------------- | ------------------------------------------ | ------------------------------------ | -------------------------------------------- |
| **Path 1: Ingestion & Enrichment** | Continuous Data Processing (The Write Path) | `Ingest → Clean → Categorize → Store`  | CREATE news records.                         |
| **Path 2: Subscription & Delivery**  | Personalized User Service (The Read Path)   | `Schedule → Filter → Aggregate → Deliver` | READ subscriptions, READ news, UPDATE delivery status. |

### High-Level Architecture Diagram

```
                               +-----------------+
                               |   News Sources  |
                               +-------+---------+
                                       |
                                       v
 PATH 1: INGESTION & ENRICHMENT ------ | ------------------------------------------------
                                       |
                                       v
                            +--------------------+
                            | Ingestion Service  |
                            +----------+---------+
                                       | (Produces to Kafka)
                                       v
                         +-----------------------------+
                         | KAFKA TOPIC: raw_news_topic |
                         +-----------------------------+
                                       | (Consumed by)
                                       v
                           +-----------------------+
                           |  Enrichment Service   |
                           | - NLP, Categorization |
                           +-----------+-----------+
                                       |           \ (Produces to Kafka)
      (Stores in DB)                   |            \
             v                         v             v
 +-----------------------+  +-------------------------+
 | Elasticsearch         |  | KAFKA TOPIC:            |
 | (News Store)          |  | cleaned_news_topic      |
 +-----------------------+  +-------------------------+
                                       |
                                       |
 PATH 2: SUBSCRIPTION & DELIVERY ----- | ------------------------------------------------
                                       |
             +-------------------------+-------------------------+
             | (Real-Time Path)                                (Batch Path)
             v                                                 v
  +--------------------+                             +---------------------+
  |    Alert Service   |                             |  Scheduler Service  |
  | - Checks breaking  |                             | - Reads Subscriptions|
  +---------+----------+                             +----------+----------+
            |                                                    | (Produces to Kafka)
            |                                                    v
            |                                      +-----------------------------+
            |                                      | KAFKA TOPIC: digest_tasks_topic |
            |                                      +-----------------------------+
            |                                                    | (Consumed by)
            |                                                    v
            |                                      +-----------------------+
            |                                      |  Aggregation Service  |
            |                                      | - Queries ES & PG     |
            |                                      +-----------+-----------+
            |                                                    |
            +---------------------+------------------------------+
                                  | (Produces to Kafka)
                                  v
                    +-----------------------------+
                    | KAFKA TOPIC: delivery_queue |
                    +-----------------------------+
                                  | (Consumed by)
                                  v
                    +-----------------------------+
                    |      Delivery Service       |
                    | - Sends Email/Push          |
                    +-----------------------------+
```

## 2. Key Technologies and Their Roles 🛠️

| Component        | Technology                  | Role in System                                                     | Why It's Used                                                              |
| ---------------- | --------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| **Message Broker**   | Kafka Cluster               | The central nervous system for asynchronous communication.         | Handles high-volume, continuous data streams and scheduling tasks.         |
| **Subscription Store** | PostgreSQL (Relational/SQL) | Stores user profiles and structured subscription preferences.      | Guarantees strong consistency for critical user data.                      |
| **News Store**       | Elasticsearch (NoSQL)       | Stores all enriched news articles with tags.                       | Optimized for fast, complex queries essential for aggregation.             |

## 3. Core Data Models 💾

*   **Subscription** (Stored in PostgreSQL)
    *   `user_id`, `selected_topics`, `selected_sources`, `delivery_schedule`, `breaking_news_enabled`
    *   **Purpose**: Defines the filtering criteria for delivery.

*   **NewsArticle** (Stored in Elasticsearch)
    *   `article_id`, `title`, `source`, `published_at`, `category_tags`, `is_breaking_news`
    *   **Purpose**: The object being filtered. The tags are the filterable metadata.

*   **DigestTask** (Kafka Message)
    *   `subscription_id`, `time_window_start`, `priority`
    *   **Purpose**: The trigger to start the aggregation process.

## 4. The Ingestion Pipeline (Path 1)

1.  **Ingestion Service**: Fetches raw data (e.g., from an RSS feed).
2.  **Produce Raw**: Publishes the raw article to Kafka: `raw_news_topic`.
3.  **Enrichment Service (Consumer)**: Reads from `raw_news_topic`.
4.  **Categorization**: Uses NLP to add `category_tags` and flags `is_breaking_news`.
5.  **Store Enriched**: Creates the final, searchable document in Elasticsearch.
6.  **Produce Cleaned**: Publishes the article ID to Kafka: `cleaned_news_topic` (for the Real-Time Alert Service).

## 5. The Delivery Pipeline (Path 2)

### A. Scheduled Digest Path (Batch)

1.  **Scheduler Service**: Reads the subscriptions table (PostgreSQL) periodically.
2.  **Produce Task**: Publishes a `DigestTask` message to Kafka: `digest_tasks_topic` for every user who is due.
3.  **Aggregation Service (Consumer)**: Reads from `digest_tasks_topic`.
4.  **Filtering/Aggregation**: Reads the user's filters from PostgreSQL, executes a complex READ query against Elasticsearch.
5.  **Delivery Staging**: Publishes the final formatted digest to Kafka: `delivery_queue_topic`.
6.  **Delivery Service**: Sends the email/push notification and UPDATES the `last_digest_sent_at` timestamp in PostgreSQL.

### B. Breaking News Path (Real-Time)

1.  **Alert Service (Consumer)**: Reads continuously from `cleaned_news_topic`.
2.  **In-Memory Match**: Instantly checks the article's tags against users who have `breaking_news_enabled = true`.
3.  **Immediate Delivery**: Publishes the alert directly to Kafka: `delivery_queue_topic` with a high priority.