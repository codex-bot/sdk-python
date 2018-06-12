import asyncio

from .lib.scheduler import Scheduler
from .lib.db import Db
from .lib.logging import Logging
from .lib.server import Server, http_response
from .components.broker import Broker
from hawkcatcher import Hawk


class CodexBot:
    # Make decorator for HTTP callback public
    http_response = http_response

    def __init__(self, application_name, host, port, db_config, token, hawk_token=None):
        """
        Initiates SDK
        """

        if not token:
            print('Please, pass your app`s token.\nYou can get it from our bot by /newapp command')
            exit()

        self.host = host
        self.port = port

        queue_name = application_name

        # Get event loop
        self.event_loop = asyncio.get_event_loop()

        self.application_name = application_name
        self.token = token

        self.user_answer_handler = None
        self.callback_query_handler = None

        self.logging = self.init_logging()
        self.db = self.init_db(db_config)
        self.scheduler = self.init_scheduler()
        self.server = self.init_server()
        self.broker = self.init_broker(application_name, queue_name)

        """
        Enable python error catcher for https://hawk.so

        You can catch any custom exception
        > try:
        >     ...
        > except:
        >     sdk.hawk.catch()
        """
        if hawk_token is not None:
            self.hawk = Hawk(hawk_token)
            self.logging.debug("Init Hawk catcher")

        self.broker.start()

    def init_logging(self):
        return Logging()

    def init_server(self):
        return Server(self.event_loop, self.host, self.port)

    def init_broker(self, application_name, queue_name):
        return Broker(self, self.event_loop, application_name, queue_name)

    def init_db(self, db_config):
        self.logging.debug("Initialize db.")
        db_name = "module_{}".format(self.application_name)
        return Db(db_name, db_config["host"], db_config["port"])

    def init_scheduler(self):
        scheduler_object = Scheduler(sdk=self)
        return scheduler_object

    def log(self, message):
        self.logging.debug(message)

    def start_server(self):
        self.server.start()

    def set_routes(self, routes):
        self.server.set_routes(routes)

    def set_path_to_static(self, route, path):
        self.server.add_static(route, path)

    def register_commands(self, commands):
        self.event_loop.run_until_complete(self.broker.api.register_commands(commands))

    def set_user_answer_handler(self, handler):
        self.user_answer_handler = handler

    def set_callback_query_handler(self, handler):
        self.callback_query_handler = handler

    async def wait_user_answer(self, user, chat, prompt=''):
        await self.broker.api.wait_user_answer(user, chat, prompt)

    async def send_text_to_chat(self, chat_hash, message, parse_mode=None, disable_web_page_preview=False, update_id=None, bot=None):
        """
        Send text message to chat

        :param chat_hash:
        :param message:
        :param parse_mode: parse mode for message. Could be Markdown or HTML
        :param disable_web_page_preview: Optional disable link preview
        :return:
        """

        payload = {
            "chat_hash": chat_hash,
            "text": message,
            "disable_web_page_preview": disable_web_page_preview,
            "bot": bot
        }

        if parse_mode:
            payload['parse_mode'] = parse_mode
        if update_id:
            payload['update_id'] = update_id

        await self.send_to_chat(payload)

    async def send_image_to_chat(self, chat_hash, photo, caption=None, bot=None):
        payload = {
            "chat_hash": chat_hash,
            "photo": photo,
            "caption": caption,
            "bot": bot
        }
        await self.send_to_chat(payload)

    async def send_inline_keyboard_to_chat(self, chat_hash, message, keyboard, bot=None):
        """
        Send inline keyboard to chat

        :param keyboard is array of button rows
        Each row is array of buttons
        Button is a dict:
            - text -- button label
            - callback_data -- (optional) string you'll get, when button is pressed
            - url -- (optional) url to open, when button is pressed


        :param chat_hash:
        :param message:
        :param keyboard:
        :return:
        """

        for row in keyboard:
            for button in row:
                button['callback_data'] = self.token + ' ' + button['callback_data']

        payload = {
            "chat_hash": chat_hash,
            "text": message,
            "markup": {
                "inline_keyboard": keyboard
            },
            "bot": bot
        }
        await self.send_to_chat(payload)

    async def send_to_chat(self, payload):
        await self.broker.api.send('send to service', payload)