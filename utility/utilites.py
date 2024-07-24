import io
import os
import yaml
import hashlib
import logging

from typing import *
from datetime import datetime
from pandas import read_csv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup
from telebot.util import quick_markup

class KangUtil:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def async_telebot(self, token: str) -> AsyncTeleBot:
        return AsyncTeleBot(token=token)
    
    def keyboard_markup(self, value: dict, row_width: int = 2) -> InlineKeyboardMarkup:
        def setup_markup(value):
            markup_dict = {}
            if isinstance(value, dict):
                for key, val in value.items():
                    markup_dict[key] = {"callback_data": key}
            return markup_dict
        
        markup = quick_markup(
            setup_markup( value ), row_width
        )
        return markup

    def format_fullname(self, message) -> str:
        return f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name

    def hashing(self, string: str, algorithm='md5') -> str:
        algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }

        if algorithm not in algorithms:
            self.logger.error(f"Unsupported algorithm '{algorithm}'. Supported algorithms are: {', '.join(algorithms.keys())}")
            return ''

        hash_object = algorithms[algorithm](string.encode())
        return hash_object.hexdigest()

    def view_log(self, log_path: str, num_bytes=1000) -> bytes:
        with open(f"{log_path}/debug.log", "rb") as file:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(max(file_size - num_bytes, 0))
            return file.read()
    
    def readline_plain(self, file: bytes):
        list_content = []
        with io.BytesIO( file ) as bfile:
            for line in bfile:
                list_content.append( line.decode( "utf-8" ).strip() )
        return list_content
    
    def readline_csv(self, file: bytes):
        with io.BytesIO( file ) as bfile:
            list_content = []

            df = read_csv( bfile )

            for index in ["_id", "id_hash", "id"]:
                try:
                    content = df[ index ].tolist()
                except (IndexError, KeyError):
                    continue
                
            for line in content:
                list_content.append( line )
        return list_content
    
    def value_in_list(self, *lists, value):
        for lst in lists:
            if value in lst: return lst
        return None
    
    def extend_key(self, *value: dict):
        return [key for define in value for key in define.keys()]
    
    def index_collection(self, config: dict):
        indexs = {
            "IPD": config[ "IPD" ], "AI": config[ "AI" ], "LOGGING": config[ "LOGGING" ]
        }
        return indexs

    def storage( self, store: dict, key: str, value: Any ): store.update( {key: value} )

    def get_config(self, path) -> dict:
        path = os.path.abspath(path)
        path = os.path.dirname(path)

        with open( f"{path}/config.yaml", "r" ) as stream:
            config = yaml.safe_load( stream )
        return config[ "config" ]

    def byters(self, string: str, doc_name: str) -> io.BytesIO:
        doc = io.BytesIO(string.encode())
        doc.name = doc_name
        return doc

    def current_datetime_str(self, format: str) -> str:
        return datetime.now().strftime(format)

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)