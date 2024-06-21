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
from logger import setup_logging
from datetime import datetime
from time import time

class OPTelebot:
    def __init__(self) -> None:
        """
        Automation to make it easier to produce data from elasticsearch query results to the specified Kafka topic.
        """
        self.config = self._config(Config) # Mengambil class Config dari file config
        self.telebot = async_telebot.AsyncTeleBot(
            token=self.config["TELEGRAM_TOKEN"]
        )
        self.query = Query(hosts=self.config["ES_URL"])
        self.send = lambda processing_path: KafkaProducerClient(
            bootstrap_servers=self.config["BOOTSTRAP_SERVER"],
            topic=self.config["TOPICS"].get(processing_path)
        )

        self.local_conf = dict()
        self.date_time = datetime.now().strftime("%Y%m%dT%H%M%S")

        setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)

        @self.telebot.message_handler(commands=["start"])
        async def start(message):
            fullname = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
            await self.telebot.send_message(
                chat_id=message.chat.id, text=(
                    f"🧑‍💻 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    "🟠 <b>Submit a list of IDs!</b>"
                ), parse_mode="HTML"
            )
            self.logger.info(f"Received /start command from {message.chat.id}")
        
        @self.telebot.message_handler(commands=["send"])
        async def send(message):
            fullname = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
            self.logger.info("Sending data to the kafka topic")
            msg = await self.telebot.send_message(
                chat_id=message.chat.id, text=(
                    f"🧑‍💻 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    "<b>🔀 Data is being sent ...</b>\n"
                    f"↳ <b>To <i>Topic {self.config['TOPICS'].get(self.local_conf['processing_path'])}</i></b>"
                ), parse_mode="HTML"
            )

            bgn = time()
            self._send_kafka()
            end = time()
            time_exec = f"{( end - bgn ):.2f}"

            await self.telebot.edit_message_text(
                chat_id=message.chat.id, message_id=msg.message_id, text=(
                    f"🧑‍💻 Req from user <i><b><a href='https://t.me/{message.from_user.username}' >SRE-{fullname}</a></b></i>\n\n"
                    f"🟢 <b>Data Successfully Sent! {time_exec}s</b>\n"
                    f"↳ <b>To <i>Topic {self.config['TOPICS'].get(self.local_conf['processing_path'])}</i></b>"
                ), parse_mode="HTML"
            )

        @self.telebot.message_handler(
            func=lambda message: True if re.match(
                pattern=r'([a-fA-F0-9]{40})\n?', string=message.text
            ) else False
        )
        async def list_id_handler(message):
            self.logger.info(f"Received valid ID: \n{message.text} \nfrom {message.chat.id}")
            
            doc = self._str_to_bytes(string=message.text, name=f"ListId-{self.date_time}.json")

            listId = message.text.split("\n")
            self.local_conf.update({"listId": listId})

            # Processing Path Options
            markup = types.InlineKeyboardMarkup()
            regular = types.InlineKeyboardButton("Regular", callback_data="regular")
            reprocess = types.InlineKeyboardButton("Reprocess", callback_data="reprocess")

            markup.add(regular, reprocess)

            await self.telebot.reply_to(message=message, text="📥 Saving ListId into a file 📁")
            await self.telebot.send_document(chat_id=message.chat.id, document=doc)
            await self.telebot.send_message(
                chat_id=message.chat.id, text="📝 Specify a processing path <b>( <i>Regular</i> OR <i>Reprocess</i> )</b>", 
                reply_markup=markup, parse_mode="HTML"
            )
        
        @self.telebot.callback_query_handler(func=lambda call: True)
        async def processing_path(call):
            self.local_conf.update({"processing_path": call.data})
            await self.telebot.send_message(chat_id=call.message.chat.id, text=(
                f"📌 <b>TOPIC <i>{self.config['TOPICS'].get(call.data)}</i></b>"
                ), parse_mode="HTML"
            )

            resp = self.query.search(ids=self.local_conf["listId"])
            self.local_conf.update({"query_result": resp})

            dumps = json.dumps(resp, indent=4)
            doc = self._str_to_bytes(string=dumps, name=f"QueryResult-{self.date_time}.json")

            await self.telebot.send_message(
                chat_id=call.message.chat.id, text=(
                    "🔎 Query results to <a href='http://10.12.3.200:5200/'>Elasticsearch</a>\n"
                    "With this Index Pattern <b>( <i>ipd-news-online*</i> )</b> can be seen below 👇"
                ), parse_mode="HTML"
            )
            await self.telebot.send_document(chat_id=call.message.chat.id, document=doc)
            await self.telebot.send_message(chat_id=call.message.chat.id, text=(
                f"✅ The data is ready to be sent to the  <b>Kafka {self.config['TOPICS'].get(self.local_conf['processing_path'])} Topic</b> 📨"
                ), parse_mode="HTML"
            )

    def _config(self, object: object):
        config = object.__dict__
        return config
    
    def _str_to_bytes(self, string: str, name: str):
        doc = io.BytesIO(string.encode())
        doc.name = name
        return doc
    
    def _send_kafka(self):
        send = self.send(processing_path=self.local_conf['processing_path'])
        for qr in self.local_conf['query_result']:
            send.send_message(message=qr)
        send.close()

    async def start_polling(self):
        await self.telebot.infinity_polling(logger_level=logging.DEBUG)

if __name__ == "__main__":
    OT = OPTelebot()
    asyncio.run(OT.start_polling())