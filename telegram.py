import re
import json
import asyncio
import logging

from typing import *
from utility import *
from time import time
from datetime import datetime
from logger import setup_logging
from library import query, kafka_producer

class BotReprocess:
    
    INDEX_PATTERNS = []
    DATETIME_FORMAT = "%Y%m%dT%H%M%S"
    PATTERN_VALIDATION_ID = r"([a-zA-Z0-9]|\d+_\d+)\n?"
    PATTERN_GT_LT = r'\{"gt": "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "lt": "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"\}'

    def __init__(self) -> None:
        """
        Automation to make it easier to produce data from elasticsearch query results to the specified Kafka topic.
        """
        self.util = kang_util()
        self.important = dict()
        self.config = self.util.get_config(__file__)
        
        self._AI = self.config[ "AI" ]
        self._IPD = self.config[ "IPD" ]
        self._HOST = self.config[ "HOST" ]
        self._PORT = self.config[ "PORT" ]
        self._FIELD = self.config[ "FIELD" ]
        self._LOG = self.config[ "LOGGING" ]
        self._ERROR = self.config[ "ERROR" ]
        self._SOURCE = self.config[ "SOURCE" ]
        self._IMA_NDC = self.config[ "IMA_NDC" ]
        self._AI_AUTH = self.config[ "AI_AUTH" ]
        self._COMPARED = self.config[ "COMPARE" ]
        self._LOG_PATH = self.config[ "LOG_PATH" ]
        self._NUM_BYTES = self.config[ "NUM_BYTES" ]
        self._AI_ES_URL = self.config[ "AI_ES_URL" ]
        self._IPD_ES_URL = self.config[ "IPD_ES_URL" ]
        self._TIME_SLEEP = self.config[ "TIME_SLEEP" ]
        self._IMA_NDC_AUTH = self.config[ "IMA_NDC_AUTH" ]
        self._IMA_NDC_ES_URL = self.config[ "IMA_NDC_ES_URL" ]
        self._LOGGING_ES_URL = self.config[ "LOGGING_ES_URL" ]
        self._TELEGRAM_TOKEN = self.config[ "TELEGRAM_TOKEN" ]
        self._BOOTSTRAP_SERVER = self.config["BOOTSTRAP_SERVER"]

        self._INDEX_COLLECTION = self.util.index_collection( self.config )
        self._EXTEND = self.util.extend_key( self._IPD, self._AI, self._LOG, self._ERROR )

        setup_logging( log_path=self._LOG_PATH )

        self.logger = self.util.get_logger( self.__class__.__name__ )
        self.telebot = self.util.async_telebot( self._TELEGRAM_TOKEN )
        self.date_time = self.util.current_datetime_str( self.DATETIME_FORMAT )

        self.http_auth = lambda auth: ( auth[ "USER" ], auth[ "PASSWORD" ] )
        self.storage = lambda key, value: self.util.storage( self.important, key, value )
        self.send = lambda topic: kafka_producer( bootstrap_servers=self._BOOTSTRAP_SERVER, topic=topic, time_sleep=self._TIME_SLEEP )


        
        @self.telebot.message_handler( commands=["start"] )
        async def start( message ):
            chat_id = message.chat.id
            initial_message = message_bot.start( message )
            await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )
            self.logger.info(f"Received /start command from {message.chat.id}")


        @self.telebot.message_handler( commands=["send"] )
        async def send( message ):
            chat_id = message.chat.id
            topic_name = self.important[ "topic_name" ]

            initial_message = message_bot.send( message, topic_name )
            save_message = await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )

            start_time = time()
            try:
                self.logger.info(f"Sending data to the Kafka topic [{topic_name}]")
                self.produce_message()
                exec_time = f"{( time() - start_time ):.2f}"    
                initial_message = message_bot.success_send( message, topic_name, exec_time )
                self.logger.info( f"Data successfully sent to Kafka topic [{topic_name}] in {exec_time}s" )
                await self.telebot.edit_message_text(
                    initial_message[ "message" ], chat_id, save_message.message_id, parse_mode=initial_message[ "parse_mode" ]
                )
            except ( KafkaErrorException, KafkaConnectionError ) as err:
                initial_message = message_bot.failed_send( message, topic_name, exec_time )
                self.logger.error(f"Error sending data to Kafka: {err}")
                await self.telebot.edit_message_text(
                    initial_message[ "message" ], chat_id, save_message.message_id, parse_mode=initial_message[ "parse_mode" ]
                )


        @self.telebot.message_handler( commands=["log"] )
        async def log( message ):
            chat_id = message.chat.id
            view_log = self.util.view_log( self._LOG_PATH, self._NUM_BYTES ).decode( "utf-8", "ignore" )
            initial_message = message_bot.view_log( message, self._HOST, self._PORT, view_log )
            await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )


        @self.telebot.message_handler( content_types=["document"] )
        async def list_id_doc( message ):
            chat_id = message.chat.id
            mime_type = message.document.mime_type
            document_file_id = message.document.file_id 

            file_info = await self.telebot.get_file(document_file_id)
            downloaded_file = await self.telebot.download_file(file_info.file_path)
            if ( mime_type == "text/plain" ):
                list_id = self.util.readline_plain( downloaded_file )
            elif ( mime_type == "text/csv" ):
                list_id = self.util.readline_csv( downloaded_file )
            elif ( mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ):
                list_id = self.util.readline_xlsx( downloaded_file ) 
            else:
                initial_message = message_bot.not_support_mime_type( message, mime_type )
                await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] ); return
            self.storage( "list_id", list_id )
            
            ids = "".join( list_id )
            fullname = self.util.format_fullname( message )
            hashing_ids = self.util.hashing( ids )
            self.logger.info( f"Received valid ID list from {chat_id} by user {fullname}: {hashing_ids}" )

            markup = self.util.keyboard_markup( self._SOURCE )
            initial_message = message_bot.markup_raw_source()
            save_message = await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ], reply_markup=markup )
            self.storage( "replay_markup_id", save_message.message_id )

        
        @self.telebot.message_handler( commands=["idcomparison"] )
        async def data_group_idcomparison(message):
            chat_id = message.chat.id
            markup = self.util.data_group_markup( self._COMPARED, 3 )
            initial_message = message_bot.markup_id_comparison()
            save_message = await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ], reply_markup=markup )
            self.storage( "replay_markup_id", save_message.message_id )
            self.storage( "idcomparison", True )
        

        @self.telebot.callback_query_handler( func=lambda call: True if call.data in self._COMPARED and self.important.get("idcomparison", False) else False )
        async def callback_handler_data_group(call):
            data = call.data
            chat_id = call.message.chat.id
            self.storage( "data_group", data )
            self.logger.info( "Users select the %s group data to compare IDs." % data )

            replay_markup_id = self.important[ "replay_markup_id" ]
            markup = self.util.filter_markup()
            await self.telebot.edit_message_reply_markup( chat_id, replay_markup_id, reply_markup=markup )

        
        @self.telebot.callback_query_handler( func=lambda call: True if re.match(self.PATTERN_GT_LT, call.data) else False )
        async def callback_handler_idcomparison(call):
            data = call.data
            chat_id = call.message.chat.id
            gt_lt = json.loads(data)
            data_group = self.important[ "data_group" ]

            field_id = self._FIELD[ "ID" ]
            field_time_source = self._FIELD[ "TIME_SOURCE" ]
            field_time_dest = self._FIELD[ "TIME_DEST" ]
            
            es_url_dest = self._IMA_NDC_ES_URL
            http_auth_dest = self.http_auth( self._IMA_NDC_AUTH )
            
            if data_group in [ "printed-news", "tv-news" ]:
                es_url = self._AI_ES_URL
                http_auth = self.http_auth( self._AI_AUTH )
                index_source = self.util.get_key_by_value( self._AI, data_group )
                index_dest = self.util.get_key_by_value( self._IMA_NDC, data_group )

            elif data_group == "online-news":
                es_url = self._IPD_ES_URL
                index_source = self._IPD.get( data_group )
                index_dest = self.util.get_key_by_value( self._IMA_NDC, data_group )

            initial_message = message_bot.currently_querying()
            save_message = await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )
            message_id = save_message.message_id

            elastic = query( hosts=es_url ) if data_group == "online-news" else query( hosts=es_url, http_auth=http_auth )
            ids = elastic.get_ids_doc( index_source, gt_lt, id=field_id, time=field_time_source )
            
            elastic = query( hosts=es_url_dest, http_auth=http_auth_dest )
            
            initial_message = message_bot.comparison_id()
            save_message = await self.telebot.edit_message_text( initial_message[ "message" ], chat_id, message_id, parse_mode=initial_message[ "parse_mode" ] )
            message_id = save_message.message_id
            
            ids_result = elastic.id_comparison_doc( index_dest, ids, id=field_id, time=field_time_dest )
            ids_result = "\n".join( ids_result )
            ids_doc = self.util.byters( ids_result, "list-id-result-comparison.txt" )
            
            initial_message = message_bot.return_ids()
            await self.telebot.edit_message_text( initial_message[ "message" ], chat_id, message_id, parse_mode=initial_message[ "parse_mode" ] )
            await self.telebot.send_document( chat_id, ids_doc )

        @self.telebot.message_handler( func=lambda message: True if re.match( self.PATTERN_VALIDATION_ID, message.text ) else False )
        async def message_id_from_user( message ):
            chat_id = message.chat.id
            message_text = message.text

            markup = self.util.keyboard_markup( self._SOURCE )
            hasing_ids = self.util.hashing( message_text )
            fullname = self.util.format_fullname( message )
            self.logger.info( f"Received valid ID list from {chat_id} by user {fullname}: {hasing_ids}" )

            file_name = "list_id%s.json" % ( self.date_time )
            file_doc = self.util.byters( message_text, file_name )
            
            list_id = message_text.split( "\n" )
            self.storage( "list_id", list_id )

            initial_message = message_bot.saving_list_id( message )
            await self.telebot.reply_to( message, initial_message[ "message" ], parse_mode=initial_message[ "parse_mode" ] )
            self.logger.info( "Saved ListId to file ListId-%s.json for user %s" % ( self.date_time, fullname ) )
            
            await self.telebot.send_document( chat_id, file_doc )

            initial_message = message_bot.markup_raw_source()
            save_message = await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ], reply_markup=markup )
            self.storage( "replay_markup_id", save_message.message_id )


        @self.telebot.callback_query_handler( func=lambda call: call.data in [ src for src in self._SOURCE.keys() ] )
        async def data_source( call ):
            source = self._SOURCE[ call.data ]
            chat_id = call.message.chat.id
            self.storage( "data_source", source )

            if ( source == "ipd" ):
                initial_message = message_bot.markup_processing_path()
                message_id = self.important[ "replay_markup_id" ]
                markup = self.util.keyboard_markup( self._IPD )
                await self.telebot.edit_message_text(
                    initial_message[ "message" ], chat_id, message_id, parse_mode=initial_message[ "parse_mode" ], reply_markup=markup
                )
            elif ( source == "ai" ):
                markup = self.util.keyboard_markup( self._AI )
                initial_message = message_bot.markup_index_pattern()
                await self.telebot.send_message(
                    chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ], reply_markup=markup
                )
            elif ( source == "logging" ):
                markup = self.util.keyboard_markup( self._LOG, row_width=1 )
                initial_message = message_bot.markup_index_pattern( kibana="LOGGING" )
                await self.telebot.send_message(
                    chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ], reply_markup=markup
                )
            elif ( source == "error" ):
                markup = self.util.keyboard_markup( self._ERROR, row_width=1 )
                initial_message = message_bot.markup_index_pattern( kibana="LOGGING" )
                await self.telebot.send_message(
                    chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ], reply_markup=markup
                )


        @self.telebot.callback_query_handler( func=lambda call: True if call.data in self._EXTEND else False)
        async def process( call ):
            call_data = call.data
            chat_id = call.message.chat.id
            username = call.from_user.username
            data_src = self.important[ "data_source" ]
            
            http_auth = None
            if ( data_src == "logging" ):
                es_url = self._LOGGING_ES_URL
                config_key = "LOGGING"
            elif ( data_src == "error" ):
                es_url = self._LOGGING_ES_URL
                config_key = "ERROR"
            elif ( data_src == "ai" ):
                es_url = self._AI_ES_URL
                http_auth = self.http_auth(
                    auth=self._AI_AUTH
                )
                config_key = "AI"
            else:
                es_url = self._IPD_ES_URL
                config_key = "IPD"

            if ( data_src == "ipd" ):
                topic_name = call_data
                index_pattern = self.config[ config_key ][ call_data ]
                self.storage( "index_pattern", index_pattern )
                self.storage( "topic_name", topic_name )
            else:
                index_pattern = call_data
                topic_name = self.config[ config_key ][ index_pattern ]
                self.storage( "index_pattern", index_pattern )
                self.storage( "topic_name", topic_name )

            self.logger.info( "User %s selected topic name: %s" % ( username, topic_name ) )
            self.logger.info( "User %s selected index pattern: %s" % ( username, index_pattern ) )
            
            initial_message = message_bot.topic_name( topic_name )
            await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )

            list_ids = self.important[ "list_id" ]
            search = query( hosts=es_url ) if not http_auth else query( hosts=es_url, http_auth=http_auth )
            response, existing_ids, ids_not_found = search.search( list_ids, index_pattern )

            self.storage( "query_result", response )
            self.logger.info( "Elasticsearch query successful for user %s" % ( username ) )

            if response:
                dumper = json.dumps( response, indent=4 ) if response else dict().__str__()
                doc_query_result = self.util.byters( dumper, "queryresult-%s.json" % ( self.date_time ) )

                initial_message = message_bot.query_result( es_url, index_pattern )
                await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )
                await self.telebot.send_document( chat_id, doc_query_result )
            
            if ids_not_found and not response:
                initial_message = message_bot.no_result_query( es_url )
                await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )
                initial_message = message_bot.not_ready_sent( topic_name )
                await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )
            
            elif ids_not_found:
                idsnf = "\n".join( ids_not_found )
                doc_ids_not_found = self.util.byters( idsnf, "list-ids-not-found.txt" )
                await self.telebot.send_document( chat_id, doc_ids_not_found )
        
            if existing_ids:    
                eids = "\n".join( existing_ids )
                doc_existing_ids = self.util.byters( eids, "list-existing-ids.txt" )
                await self.telebot.send_document( chat_id, doc_existing_ids )
                initial_message = message_bot.ready_sent( topic_name )
                await self.telebot.send_message( chat_id, initial_message[ "message" ], initial_message[ "parse_mode" ] )

    def produce_message(self):
        '''
        Function untuk mengirimkan data ke Topic kafka yang ditentukan
        '''
        send_message = self.send( self.important[ "topic_name" ] )
        for message in self.important[ "query_result" ]:
            send_message.send_message( message )
            self.logger.info( message.__str__() )
        send_message.close()

    async def start_polling(self):
        '''
        Menjalankan bot polling telebot
        '''
        self.logger.info("Starting bot polling...")
        await self.telebot.infinity_polling(logger_level=logging.DEBUG)
        self.logger.info("Bot polling has stopped.")

if __name__ == "__main__":
    OT = BotReprocess()
    try:
        asyncio.run(OT.start_polling())
    except (KeyboardInterrupt, SystemExit):
        OT.logger.info("Bot stopped by user.")
    except Exception as e:
        OT.logger.error(f"Unexpected error: {e}")
