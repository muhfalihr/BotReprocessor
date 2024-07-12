import re
import json
import logging

from flask_restx import Api, Resource, fields
from flask import Flask, request, Response
from config import Config
from elasticsearch import Elasticsearch
from kafka import KafkaProducer
from logger import setup_logging
from typing import *
# from library.elastic import Query
# from library.kafkaclient import KafkaProducerClient

class Query:
    def __init__(self, **kwargs) -> None:
        """
        Inisialisasi Elasticsearch dengan konfigurasi yang diberikan.

        :params hosts: Host dari Elasticsearch
        """
        self.es = Elasticsearch(**kwargs, headers={"Content-Type": "application/json"})
    
    def search(self, ids: List[str]):
        """
        Mencari document di setiap index berdasarkan IDs yang diberikan.

        :params ids: List id
        """
        responses = [
            doc.get("_source")
            for id in ids
            for doc in self.es.search(
                index="_all",
                body={
                    "query": {
                        "match": {
                            "_id": id
                        }
                    }
                }
            ).get("hits").get("hits")
        ]
        return responses

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
            ...
    
    def close(self):
        """
        Menutup KafkaProducer.
        """
        self.producer.close()

app = Flask(__name__)
app.config.from_object(Config)

api = Api(app, version="1.0.0", title="Online News Processing API", description=app.config["API_DESC"])

ns1 = api.namespace("OnlineNewsProcessing", description="Operations related to online news processing")

model = [fields.String(reqired=True, description='ID online-news')]

@ns1.route('/api')
class OnlineNewsProcessing(Resource):
    def __init__(self, api=None, *args, **kwargs):
        super().__init__(api, *args, **kwargs)
        
        setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

    @ns1.response(200, "OK")
    @ns1.response(400, "Bad Request")
    @ns1.response(500, "Internal Server Error")
    @ns1.expect(model)
    @ns1.doc(
        params={
            "processing_path": {
                "description": "specify a processing path (regular or reprocess)",
                "enum": [p for p in ["regular", "reprocess"]],
                "required": True,
                "default": "regular"
            }
        }
    )
    def post(self):
        """Online News Processing"""
        def data_validation(data: Any):
            if isinstance(data, list) and all(isinstance(d, str) for d in data):
                return data, 200
            return {}, 400
        
        try:
            ids = api.payload
            processing_path = request.values.get("processing_path")
            validation = data_validation(data=ids)

            if validation[1] != 200:
                return {"message": "Invalid Data", "payload": ids}, validation[1]

            q = Query(hosts=app.config["ES_URL"])
            k = KafkaProducerClient(
                bootstrap_servers=app.config["BOOTSTRAP_SERVER"], 
                topic=app.config["TOPICS"].get(processing_path)
            )

            responses = q.search(ids=ids)
            for response in responses:
                k.send_message(message=response)
            k.close()

            return {"message": "Data Successfully Sent", "datas": responses}, 200
        except Exception as err:
            return {"message" f"Internal Server Error: {err}"}, 500

if __name__ == "__main__":
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=True)