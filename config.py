class Config:
    # Log
    LOG_PATH = "/tmp/onp"
    NUM_BYTES = 3900

    # Elasticsearch
    IPD_ES_URL = "http://10.12.3.200:5200/"
    LOGGING_ES_URL = "http://192.168.21.100:5200/"

    # Kafka
    BOOTSTRAP_SERVER = ['kafka01.production02.bt:9092','kafka02.production02.bt:9092','kafka03.production02.bt:9092','kafka04.production02.bt:9092','kafka05.production02.bt:9092','kafka06.production02.bt:9092']
    TOPICS = {
        "regular": "online-news",
        "regular-flag": "online-news-flag",
        "reprocess": "online-news-reprocess"
    }

    # Define Host and Port for log app
    HOST = "192.168.20.136"
    PORT = "9898"

    # Telegram
    TELEGRAM_TOKEN = "7489023152:AAF95SiNy4A8MC4nzEDNEmLOqpEqGW4mnIM"
    GROUP_ID = "-4244608457"

    # API Description
    API_DESC = """
The Online News Processing API allows users to submit a list of online news IDs and specify a processing path (regular or reprocess).
The API queries the provided IDs from ElasticSearch, retrieves the relevant data from the _source field, and pushes the data to a Kafka topic based on the chosen processing path.
When the 'regular' path is selected, data is pushed to the 'online-news' topic. When the 'reprocess' path is chosen, data is pushed to the 'online-news-reprocess' topic.
This API streamlines the processing and reprocessing of online news data for seamless integration and efficient data handling.
"""
