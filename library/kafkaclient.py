import time
import json
import logging

from confluent_kafka import Producer, KafkaException, KafkaError

class KafkaProducerClient:
    def __init__(self, **config) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bootstrap_servers = ",".join(config.get("bootstrap_servers"))
        self.topic = config.get("topic")
        self.time_sleep = config.get("time_sleep")

        self.producer = Producer({
            'bootstrap.servers': self.bootstrap_servers
        })

    def delivery_report(self, err, msg):
        if err is not None:
            self.logger.error(f"Message delivery failed: {err}")
        else:
            self.logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send_message(self, message):
        try:
            self.producer.produce(
                topic=self.topic,
                value=json.dumps(message).encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.flush()
            time.sleep(self.time_sleep)
        except KafkaException as err:
            self.logger.error(f"Kafka Error : {err}")
        except Exception as err:
            self.logger.error(f"Kafka Error : {err}")

    def close(self):
        self.producer.flush()
