import json

from kafka import KafkaProducer

class KafkaProducerClient:
    def __init__(self, **config) -> None:
        """
        Inisialisasi KafkaProducerClient dengan konfigurasi yang diberikan.
        
        :param bootstrap_servers: Daftar alamat server bootstrap Kafka.
        :param topic: Topik Kafka tempat pesan akan diproduksi.
        """
        self.bootstrap_servers = config.get("bootstrap_servers")
        self.topic = config.get("topic")
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            api_version=(3, 7, 0),
            security_protocol='PLAINTEXT',
            request_timeout_ms=60000,
            retries=5,
            retry_backoff_ms=200,
            connections_max_idle_ms=60000
        )

    def send_message(self, message):
        """
        Mengirim pesan ke topik Kafka yang dikonfigurasi.
        
        :param message: Pesan yang akan dikirim (format dict).
        """
        try:
            self.producer.send(topic=self.topic, value=message)
        except Exception as err:
            raise err
    
    def close(self):
        """
        Menutup KafkaProducer.
        """
        self.producer.close()
