import io
import re
import asyncio
import logging
import json

from typing import *
from config import Config
from telebot import types, async_telebot
from utility.utilites import *
from library.elastic import Query
from library.kafkaclient import KafkaProducerClient
from kafka import errors as kafka_errors
from logger import setup_logging
from datetime import datetime
from time import time

class OPTelebot:
    def __init__(self) -> None:
        """
        Automation to make it easier to produce data from elasticsearch query results to the specified Kafka topic.
        """
        self.config = self._config(Config) # mengambil konfigurasi di file config.py

        setup_logging(log_path=self.config["LOG_PATH"]) # setup log dengan path yang ditentukan
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # mendefinisikan telebot dengan tokennya
        self.telebot = async_telebot.AsyncTeleBot(
            token=self.config["TELEGRAM_TOKEN"]
        )

        # mendefinisikan class KafkaProducerClient
        self.send = lambda topic: KafkaProducerClient(
            bootstrap_servers=self.config["BOOTSTRAP_SERVER"],
            topic=self.config["TOPICS"].get(topic)
        )

        self.local_conf = dict() # konfigurasi dari hasil interaksi dengan user
        self.date_time = datetime.now().strftime("%Y%m%dT%H%M%S")

        # Meresponse message /start dari user
        @self.telebot.message_handler(commands=["start"])
        async def start(message):
            '''
            Memulai Program. User disuruh mengirimkan List ID.
            '''
            fullname = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
            await self.telebot.send_message(
                chat_id=message.chat.id, text=(
                    f"👤 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    "🟠 <b>Submit a list of IDs!</b>"
                ), parse_mode="HTML"
            )
            self.logger.info(f"Received /start command from {message.chat.id}")
        
        # Meresponse message /send dari user
        @self.telebot.message_handler(commands=["send"])
        async def send(message):
            '''
            Mengirimkan data ke Topic Kafka yang ditentukan.
            '''
            fullname = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
            topic_name = self.local_conf['topic']
            
            msg = await self.telebot.send_message(
                chat_id=message.chat.id, text=(
                    f"👤 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    "<b>🔀 Data is being sent ...</b>\n"
                    f"↳ <b>To <i>Topic {topic_name}</i></b>"
                ), parse_mode="HTML"
            )

            bgn = time() # Waktu mulai
            iserror = False # untuk pengkondisian error

            try:
                self.logger.info(f"Sending data to the Kafka topic [{topic_name}] for user {fullname}")
                self._send_kafka() # Mengirim data ke topic kafka

                end = time() # Waktu henti
                time_exec = f"{( end - bgn ):.2f}" # Waktu yang diperlukan untuk mengirim data ke Topic Kafka
                
                self.logger.info(
                    f"Data successfully sent to Kafka topic [{topic_name}] in {time_exec}s for user {fullname}"
                )
            except kafka_errors.KafkaError as err:
                self.logger.error(f"Error sending data to Kafka: {err}")
                time_exec = "N/A"
                iserror = True

            await self.telebot.edit_message_text(
                chat_id=message.chat.id, message_id=msg.message_id, text=(
                    f"👤 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    f"🟢 <b>Data Successfully Sent! {time_exec}s</b>\n"
                    f"↳ <b>To <i>Topic {topic_name}</i></b>"
                ) if not iserror else (
                    f"👤 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    f"🔴 <b>Error sending data! {time_exec}s</b>\n"
                    f"↳ <b>To <i>Topic {topic_name}</i></b>"
                ), parse_mode="HTML"
            )
        
        # Meresponse message /log dari user
        @self.telebot.message_handler(commands=["log"])
        async def log(message):
            '''
            Menampilkan Log ke User. Dengan ukuran default 1000 bytes.
            '''
            fullname = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
            last_logs = view_log(log_path=self.config["LOG_PATH"], num_bytes=self.config["NUM_BYTES"]) # Mengambil last log dengan ukuran 1000 bytes
            view_last_log = last_logs.decode(encoding="utf-8", errors="ignore") # Mendecode bytes ke utf-8 dan mengabaikan error

            await self.telebot.send_message(
                chat_id=message.chat.id, text=(
                    f"👤 Req from user [SRE-{fullname}](https://t.me/{message.from_user.username})\n\n"
                    "See [Full Log](http://192.168.20.136:9898/log) details.\n\n"
                    f"```\n{view_last_log}```"
                ), parse_mode="Markdown"
            )

        # Mersponse message List Id yang cocok dengan pattern regex ini
        @self.telebot.message_handler(
            func=lambda message: True if re.match(
                pattern=r'([a-zA-Z0-9]|\d+_\d+)\n?', string=message.text
            ) else False
        )
        async def list_id_handler(message):
            '''
            Menangkap List ID dari User dan di simpan ke local conf
            '''
            fullname = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
            self.logger.info(f"Received valid ID list from {message.chat.id} by user {fullname}: {hashing(message.text)}")
            
            # Menjadikan message text ke bytes
            doc = self._str_to_bytes(string=message.text, name=f"ListId-{self.date_time}.json")

            # Mengubah List ID dari string ke List dan menambahkannya ke local conf
            listId = message.text.split("\n")
            self.local_conf.update({"listId": listId})

            markup = types.InlineKeyboardMarkup()
            logging = types.InlineKeyboardButton("Logging", callback_data="logging")
            ipd = types.InlineKeyboardButton("IPD", callback_data="ipd")
            markup.add(logging, ipd)

            await self.telebot.reply_to(
                    message=message, text=(
                       f"👤 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                        "📥 Saving ListId into a file 📁"
                    ), parse_mode="HTML"
            )
            self.logger.info(f"Saved ListId to file ListId-{self.date_time}.json for user {fullname}")

            await self.telebot.send_document(chat_id=message.chat.id, document=doc)
            msg = await self.telebot.send_message(
                chat_id=message.chat.id, text="🌞 Specify a data raw source from <b>( <i>Logging</i> OR <i>IPD</i> )</b>", 
                reply_markup=markup, parse_mode="HTML"
            )
            self.local_conf.update({"replay_markup_id": msg.message_id})
        
        @self.telebot.callback_query_handler(func=lambda call: call.data in ["ipd", "logging"])
        async def ipd_handler(call):
            # Processing Path Options
            if call.data == "ipd":
                path1, path2 = "Regular", "Reprocess"
                self.local_conf.update({"data_source": call.data})
                self.local_conf.update({"index": "ipd-news-online*"})
                markup = types.InlineKeyboardMarkup()
                regular = types.InlineKeyboardButton("Regular", callback_data="online-news")
                reprocess = types.InlineKeyboardButton("Reprocess", callback_data="online-news-reprocess")
                markup.add(regular, reprocess)

                msg_id = self.local_conf.get("replay_markup_id")

                await self.telebot.edit_message_text(
                    chat_id=call.message.chat.id, message_id=msg_id, text=f"📝 Specify a processing path <b>( <i>{path1}</i> OR <i>{path2}</i> )</b>", 
                    reply_markup=markup, parse_mode="HTML"
                )
            else:
                self.local_conf.update({"data_source": call.data})

                index_markup = types.InlineKeyboardMarkup()
                facebook_comment = types.InlineKeyboardButton("logging-result-facebook-comment-*", callback_data="logging-result-facebook-comment-*")
                facebook_post = types.InlineKeyboardButton("logging-result-facebook-post-*", callback_data="logging-result-facebook-post-*")
                instagram_comment = types.InlineKeyboardButton("logging-result-instagram-comment-*", callback_data="logging-result-instagram-comment-*")
                instagram_post = types.InlineKeyboardButton("logging-result-instagram-post-*", callback_data="logging-result-instagram-post-*")
                online_news = types.InlineKeyboardButton("logging-result-online-news-*", callback_data="logging-result-online-news-*")
                printed_news = types.InlineKeyboardButton("logging-result-printed-news-*", callback_data="logging-result-printed-news-*")
                tiktok_comment = types.InlineKeyboardButton("logging-result-tiktok-comment-*", callback_data="logging-result-tiktok-comment-*")
                tiktok_post = types.InlineKeyboardButton("logging-result-tiktok-post-*", callback_data="logging-result-tiktok-post-*")
                tv_news = types.InlineKeyboardButton("logging-result-tv-news-*", callback_data="logging-result-tv-news-*")
                twitter_post = types.InlineKeyboardButton("logging-result-twitter-post-*", callback_data="logging-result-twitter-post-*")
                youtube_comment = types.InlineKeyboardButton("logging-result-youtube-comment-*", callback_data="logging-result-youtube-comment-*")
                youtube_post = types.InlineKeyboardButton("logging-result-youtube-post-*", callback_data="logging-result-youtube-post-*")
                index_markup.add(
                    facebook_comment, facebook_post, instagram_comment, instagram_post, online_news, printed_news,
                    tiktok_comment, tiktok_post, tv_news, twitter_post, youtube_comment, youtube_post, row_width=1
                )
                await self.telebot.send_message(
                    chat_id=call.message.chat.id, text="🎞 Specify a index pattern for <b>( <i>Logging</i> )</b>", 
                    reply_markup=index_markup, parse_mode="HTML"
                )
        
        # Menghandle call untuk mengambil value nya
        @self.telebot.callback_query_handler(func=lambda call: call.data in ["online-news", "online-news-reprocess"])
        async def define_topic(call):
            '''
            Melakukan query ke elasticsearch berdasarkan IDs yang dikirim oleh User.
            Dan hasil query tersebut akan dikirimkan ke User.
            '''
            self.local_conf.update({"topic": call.data})
            self.logger.info(f"User {call.from_user.username} selected processing path: {call.data}")

            await self.telebot.send_message(chat_id=call.message.chat.id, text=(
                f"📌 <b>TOPIC <i>{call.data}</i></b>"
                ), parse_mode="HTML"
            )

            try:
                # Melakukan query searching ke index dan id yang ditentukan
                query = Query(hosts=self.config["IPD_ES_URL"])
                resp = query.search(ids=self.local_conf["listId"], index_pattern=self.local_conf.get("index"))
                self.local_conf.update({"query_result": resp}) # Menyimpan hasil query ke local conf
                self.logger.info(f"Elasticsearch query successful for user {call.from_user.username}")
            except Exception as err:
                self.logger.error(f"{err}")
                resp = {}
                self.local_conf.update({"query_result": resp})

            dumps = json.dumps(resp, indent=4) if resp else dict().__str__() # Menjadikan hasil query yang awalnya list json ke string
            doc = self._str_to_bytes(string=dumps, name=f"QueryResult-{self.date_time}.json") if resp else ... # Mengubah string ke bytes untuk dijadikan file

            await self.telebot.send_message(
                chat_id=call.message.chat.id, text=(
                    f"🔎 Query results to <a href='{self.config['IPD_ES_URL']}'>Elasticsearch</a>\n"
                    f"With this Index Pattern <b>( <i>{self.local_conf.get('index')}</i> )</b> can be seen below 👇"
                ) if resp else (
                    "🚨 No results found for query Elasticsearch. Check /log for details."
                ), parse_mode="HTML"
            )
            await self.telebot.send_document(chat_id=call.message.chat.id, document=doc) if resp else ...
            await self.telebot.send_message(chat_id=call.message.chat.id, text=(
                f"✅ The data is ready to be sent to the  <b>Kafka {self.local_conf['topic']} Topic</b> 📨"
                ) if resp else (
                    f"⛔ The data is not ready to be sent to the <b>Kafka {self.local_conf['topic']} Topic</b>"
                ), parse_mode="HTML"
            )

        @self.telebot.callback_query_handler(func=lambda call: re.match(pattern=r'logging-result.*', string=call.data))
        async def query_elastic(call):
            self.local_conf.update({"index": call.data})
            self.logger.info(f"User {call.from_user.username} selected index pattern: {call.data}")

            await self.telebot.send_message(
                chat_id=call.message.chat.id, text=f"📌 <b>Index Pattern for queries is <i>{call.data}</i></b>", parse_mode="HTML"
            )

            specify_topic = self.specify_topic(index_pattern=call.data)
            topic = self.config["TOPICS"].get(specify_topic)
            self.local_conf.update({"topic": topic})

            await self.telebot.send_message(chat_id=call.message.chat.id, text=(
                f"📌 <b>TOPIC <i>{topic}</i></b>"
                ), parse_mode="HTML"
            )

            try:
                # Melakukan query searching ke index dan id yang ditentukan
                query = Query(hosts=self.config["LOGGING_ES_URL"])
                resp = query.search(ids=self.local_conf["listId"], index_pattern=self.local_conf.get("index"))
                self.local_conf.update({"query_result": resp}) # Menyimpan hasil query ke local conf
                self.logger.info(f"Elasticsearch query successful for user {call.from_user.username}")
            except Exception as err:
                self.logger.error(f"{err}")
                resp = {}
                self.local_conf.update({"query_result": resp})

            dumps = json.dumps(resp, indent=4) if resp else dict().__str__() # Menjadikan hasil query yang awalnya list json ke string
            doc = self._str_to_bytes(string=dumps, name=f"QueryResult-{self.date_time}.json") if resp else ... # Mengubah string ke bytes untuk dijadikan file

            await self.telebot.send_message(
                chat_id=call.message.chat.id, text=(
                    f"🔎 Query results to <a href='{self.config['LOGGING_ES_URL']}'>Elasticsearch</a>\n"
                    f"With this Index Pattern <b>( <i>{self.local_conf.get('index')}</i> )</b> can be seen below 👇"
                ) if resp else (
                    "🚨 No results found for query Elasticsearch. Check /log for details."
                ), parse_mode="HTML"
            )
            await self.telebot.send_document(chat_id=call.message.chat.id, document=doc) if resp else ...
            await self.telebot.send_message(chat_id=call.message.chat.id, text=(
                f"✅ The data is ready to be sent to the  <b>Kafka {topic} Topic</b> 📨"
                ) if resp else (
                    f"⛔ The data is not ready to be sent to the <b>Kafka {topic} Topic</b>"
                ), parse_mode="HTML"
            )


        # Menghandle message yang tidak diketahui atau tidak sesuai
        @self.telebot.message_handler(func=lambda message: True)
        async def instruction(message):
            '''
            handling message yang tidak dikethui atau tidak sesuai dari User
            '''
            await self.telebot.send_message(chat_id=message.chat.id, text="Unrecognized command. Say what?")
    
    def specify_topic(self, index_pattern: str):
        if re.match(r'.*-facebook-comment-\*', index_pattern):
            return "facebook-comment"
        if re.match(r'.*-facebook-post-\*', index_pattern):
            return "facebook-post"
        if re.match(r'.*-instagram-comment-\*', index_pattern):
            return "instagram-comment"
        if re.match(r'.*-instagram-post-\*', index_pattern):
            return "instagram-post"
        if re.match(r'.*-online-news-\*', index_pattern):
            return "online-news-flag"
        if re.match(r'.*-printed-news-\*', index_pattern):
            return "printed-news"
        if re.match(r'.*-tiktok-comment-\*', index_pattern):
            return "tiktok-comment"
        if re.match(r'.*-tiktok-post-\*', index_pattern):
            return "tiktok-post"
        if re.match(r'.*-tv-news-\*', index_pattern):
            return "tv-news"
        if re.match(r'.*-twitter-post-\*', index_pattern):
            return "twitter-post"
        if re.match(r'.*-youtube-comment-\*', index_pattern):
            return "youtube-comment"
        if re.match(r'.*-youtube-post-\*', index_pattern):
            return "youtube-post"
        

    def _config(self, object: object):
        '''
        Menjadikan value dari object ke dictionary

        Argument:
            object (object): Object
        
        Returns:
            object.__dict__ (dict)
        '''
        config = object.__dict__
        return config
    
    def _str_to_bytes(self, string: str, name: str):
        '''
        Mengubah string ke bytes
        '''
        doc = io.BytesIO(string.encode())
        doc.name = name
        self.logger.debug(f"Converted string to bytes with name {name}")
        return doc
    
    def _send_kafka(self):
        '''
        Function untuk mengirimkan data ke Topic kafka yang ditentukan
        '''
        send = self.send(topic=self.local_conf['topic'])
        for qr in self.local_conf['query_result']:
            send.send_message(message=qr)
            self.logger.info(qr.__str__())
        send.close()

    async def start_polling(self):
        '''
        Menjalankan bot polling telebot
        '''
        self.logger.info("Starting bot polling...")
        await self.telebot.infinity_polling(logger_level=logging.DEBUG)
        self.logger.info("Bot polling has stopped.")

if __name__ == "__main__":
    OT = OPTelebot()
    try:
        asyncio.run(OT.start_polling())
    except (KeyboardInterrupt, SystemExit):
        OT.logger.info("Bot stopped by user.")
    except Exception as e:
        OT.logger.error(f"Unexpected error: {e}")
