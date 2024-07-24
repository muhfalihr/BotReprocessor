import time
import json
import logging

from kafka import KafkaProducer, errors as kafka_errors

class KafkaProducerClient:
    '''
    A class used to produce messages to a Kafka topic.

    Attributes
    ----------
    bootstrap_servers : str
        A list of Kafka bootstrap server addresses.
    topic : str
        The Kafka topic to which messages will be sent.
    producer : KafkaProducer
        An instance of the KafkaProducer client configured with the provided settings.

    Methods
    -------
    send_message(message: dict) -> None
        Sends a message to the configured Kafka topic.
    close() -> None
        Closes the KafkaProducer instance.
    '''
    def __init__(self, **config) -> None:
        """
        Initializes the KafkaProducerClient with the provided configuration.

        Parameters
        ----------
        config : dict
            Configuration dictionary containing the bootstrap servers and topic.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bootstrap_servers = config.get("bootstrap_servers")
        self.topic = config.get("topic")
        self.time_sleep = config.get("time_sleep")
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

    def send_message(self, message):
        """
        Sends a message to the configured Kafka topic.

        Parameters
        ----------
        message : dict
            The message to be sent to the Kafka topic.
        
        Raises
        ------
        kafka_errors.KafkaError
            If there is an error sending the message to Kafka.
        Exception
            If there is a general error.
        """
        try:
            self.producer.send(topic=self.topic, value=message)
            time.sleep(self.time_sleep)
        except kafka_errors.KafkaError as err:
            self.logger.error(f"Kafka Error : {err}")
        except Exception as err:
            self.logger.error(f"Kafka Error : {err}")
    
    def close(self):
        """
        Closes the KafkaProducer instance.
        """
        self.producer.close()