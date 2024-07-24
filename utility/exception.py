from kafka import errors
from elasticsearch import ElasticsearchException

class KafkaErrorException(errors.KafkaError):
    pass

class KafkaConnectionError(errors.KafkaConnectionError):
    pass

class ElasticsearchErrorException(ElasticsearchException, Exception):
    pass