class Config:
    # Log
    LOG_PATH = "/tmp/onp"
    NUM_BYTES = 3900

    # Elasticsearch
    IPD_ES_URL = "<ES_URL>"
    LOGGING_ES_URL = "<ES_URL>"

    # Kafka
    BOOTSTRAP_SERVER = ['kafka01.production02.bt:9092','kafka02.production02.bt:9092','kafka03.production02.bt:9092','kafka04.production02.bt:9092','kafka05.production02.bt:9092','kafka06.production02.bt:9092']
    TOPICS = {
        "online-news": "online-news",
        "online-news-reprocess": "online-news-reprocess",
        "facebook-post": "ipd-facebook-post-flag",
        "facebook-comment": "ipd-facebook-comment-flag",
        "instagram-comment": "ipd-instagram-comment-flag",
        "instagram-post": "ipd-instagram-post-flag",
        "online-news-flag": "online-news-flag",
        "printed-news": "printed-news-flag",
        "tiktok-comment": "ipd-tiktok-comment-flag",
        "tiktok-post": "ipd-tiktok-post-flag",
        "tv-news": "tv-news-flag",
        "twitter-post": "ipd-twitter-post-flag",
        "youtube-comment": "ipd-youtube-comment-flag",
        "youtube-post": "ipd-youtube-post-flag"
    }

    # Define Host and Port for log app
    HOST = "<HOST>"
    PORT = "<PORT>"

    # Telegram
    TELEGRAM_TOKEN = "<TOKEN>"
    GROUP_ID = "<GROUP_ID>"

    # API Description
    API_DESC = """
The Online News Processing API allows users to submit a list of online news IDs and specify a processing path (regular or reprocess).
The API queries the provided IDs from ElasticSearch, retrieves the relevant data from the _source field, and pushes the data to a Kafka topic based on the chosen processing path.
When the 'regular' path is selected, data is pushed to the 'online-news' topic. When the 'reprocess' path is chosen, data is pushed to the 'online-news-reprocess' topic.
This API streamlines the processing and reprocessing of online news data for seamless integration and efficient data handling.
"""
