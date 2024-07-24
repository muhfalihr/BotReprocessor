from typing import *

class MessageBot:
    @staticmethod
    def _format_fullname(message) -> str:
        return f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name

    @staticmethod
    def _create_message(username: str, fullname: str, content: str, parse_mode: str = "HTML") -> Dict[str, str]:
        return {
            "message": (
                f"👤 Req from user <i><b><a href='https://t.me/{username}' >SRE-{fullname}</a></b></i>\n\n{content}"
            ),
            "parse_mode": parse_mode
        }
    
    @staticmethod
    def _create_simple_message(content: str, parse_mode: str = "HTML") -> Dict[str, str]:
        return {"message": content, "parse_mode": parse_mode}
    
    @staticmethod
    def start(message) -> Dict[str, str]:
        fullname = MessageBot._format_fullname(message)
        content = "🟠 <b>Submit a list of IDs!</b>"
        return MessageBot._create_message(message.from_user.username, fullname, content)

    @staticmethod
    def send(message, topic_name) -> Dict[str, str]:
        fullname = MessageBot._format_fullname(message)
        content = f"<b>🔀 Data is being sent ...</b>\n↳ <b>To <i>Topic {topic_name}</i></b>"
        return MessageBot._create_message(message.from_user.username, fullname, content)

    @staticmethod
    def success_send(message, topic_name, time_exec) -> Dict[str, str]:
        fullname = MessageBot._format_fullname(message)
        content = f"🟢 <b>Data Successfully Sent! {time_exec}s</b>\n↳ <b>To <i>Topic {topic_name}</i></b>"
        return MessageBot._create_message(message.from_user.username, fullname, content)
    
    @staticmethod
    def saving_list_id(message):
        fullname = MessageBot._format_fullname(message)
        content = "📥 Saving ListId into a file 📁"
        return MessageBot._create_message(message.from_user.username, fullname, content)

    @staticmethod
    def failed_send(message, topic_name, time_exec) -> Dict[str, str]:
        fullname = MessageBot._format_fullname(message)
        content = f"🔴 <b>Error sending data! {time_exec}s</b>\n↳ <b>To <i>Topic {topic_name}</i></b>"
        return MessageBot._create_message(message.from_user.username, fullname, content)
    
    @staticmethod
    def view_log(message, host, port, log) -> Dict[str, str]:
        fullname = MessageBot._format_fullname(message)
        content = f"See [Full Log](http://{host}:{port}/log) details.\n\n```\n{log}```"
        return MessageBot._create_message(message.from_user.username, fullname, content, "Markdown")
    
    @staticmethod
    def markup_message(content: str) -> Dict[str, str]:
        return {"message": content, "parse_mode": "HTML"}

    @staticmethod
    def markup_raw_source() -> Dict[str, str]:
        content = "🌞 Specify a data raw source from <b>( <i>AI</i> OR <i>LOGGING</i> OR <i>IPD</i> OR <i>ERROR</i> )</b>"
        return MessageBot.markup_message(content)
    
    @staticmethod
    def markup_processing_path() -> Dict[str, str]:
        content = "📝 Specify a processing path <b>( <i>Regular</i> OR <i>Reprocess</i> )</b>"
        return MessageBot.markup_message(content)
    
    @staticmethod
    def markup_index_pattern(kibana="AI") -> Dict[str, str]:
        content = f"🎞 Specify a index pattern for <b>( <i>{kibana}</i> )</b>"
        return MessageBot.markup_message(content)
    
    @staticmethod
    def topic_name(topic: str) -> Dict[str, str]:
        content = f"📌 <b>TOPIC <i>{topic}</i></b>"
        return MessageBot._create_simple_message(content)
    
    @staticmethod
    def query_result(es_url: str, index_pattern: str) -> Dict[str, str]:
        content = f"🔎 Query results to <a href='{es_url}'>Elasticsearch</a>\nWith this Index Pattern <b>( <i>{index_pattern}</i> )</b> can be seen below 👇"
        return MessageBot._create_simple_message(content)
    
    @staticmethod
    def no_result_query(es_url: str) -> Dict[str, str]:
        content = "🚨 No results found for query <a href='{es_url}'>Elasticsearch</a>. Check /log for details."
        return MessageBot._create_simple_message(content)
    
    @staticmethod
    def ready_sent(topic: str) -> Dict[str, str]:
        content = f"✅ The data is ready to be sent to the <b>Kafka {topic} Topic</b> 📨"
        return MessageBot._create_simple_message(content)
    
    @staticmethod
    def not_ready_sent(topic: str) -> Dict[str, str]:
        content = f"⛔ The data is not ready to be sent to the <b>Kafka {topic} Topic</b>"
        return MessageBot._create_simple_message(content)
    
    @staticmethod
    def index_pattern(index_pattern: str) -> Dict[str, str]:
        content = f"📌 <b>Index Pattern for queries is <i>{index_pattern}</i></b>"
        return MessageBot._create_simple_message(content)
