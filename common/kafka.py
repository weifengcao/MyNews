"""Utilities for producing to and consuming from Kafka topics."""
import json
import logging

from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

from common import config


def create_kafka_producer():
    """Creates and returns a Kafka producer configured for JSON payloads."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BROKER,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            retries=5,
            linger_ms=10,
        )
        logging.info("Kafka producer created successfully.")
        return producer
    except NoBrokersAvailable:
        logging.error("Could not connect to Kafka broker at %s.", config.KAFKA_BROKER)
        return None


def create_kafka_consumer(topic: str, group_id: str):
    """Creates and returns a Kafka consumer for a given topic and group."""
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=config.KAFKA_BROKER,
            auto_offset_reset="earliest",
            group_id=group_id,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        logging.info("Kafka consumer for topic '%s' created successfully.", topic)
        return consumer
    except NoBrokersAvailable:
        logging.error("Could not connect to Kafka broker at %s.", config.KAFKA_BROKER)
        return None
