"""Utility consumer that prints messages from a Kafka topic."""
import argparse
import logging

from common import config
from common.kafka import create_kafka_consumer

logging.basicConfig(level=logging.INFO, format=config.LOG_FORMAT)


def consume(topic: str) -> None:
    consumer = create_kafka_consumer(topic, "log-consumer")
    if not consumer:
        logging.critical("Cannot consume topic %s without Kafka connectivity.", topic)
        return

    logging.info("Consuming messages from topic: %s", topic)
    for message in consumer:
        logging.info("%s", message.value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log Kafka topic messages.")
    parser.add_argument("topic", nargs="?", default=config.DELIVERY_QUEUE_TOPIC)
    args = parser.parse_args()
    consume(args.topic)
