class Config:
    # Log
    LOG_PATH = "/tmp/onp"
    NUM_BYTES = 1000

    # Elasticsearch
    ES_URL = "http://10.12.3.200:5200/"
    ES_HOST = "10.12.3.200"

    # Kafka
    BOOTSTRAP_SERVER = ["10.0.0.12:9092"]
    TOPICS = {
        "regular": "online-news",
        "reprocess": "online-news-reprocess"
    }

    # Define Host and Port
    HOST = "10.1.62.33"
    PORT = "9090"

    # Telegram
    TELEGRAM_TOKEN = "6991087594:AAHwt9o0a0Dpji8TA-1-jVV5B2_fWbVzoSg"
    GROUP_ID = "-4244608457"

    # API Description
    API_DESC = """
The Online News Processing API allows users to submit a list of online news IDs and specify a processing path (regular or reprocess).
The API queries the provided IDs from ElasticSearch, retrieves the relevant data from the _source field, and pushes the data to a Kafka topic based on the chosen processing path.
When the 'regular' path is selected, data is pushed to the 'online-news' topic. When the 'reprocess' path is chosen, data is pushed to the 'online-news-reprocess' topic.
This API streamlines the processing and reprocessing of online news data for seamless integration and efficient data handling.
"""
