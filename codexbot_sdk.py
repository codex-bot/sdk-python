import asyncio

from .lib.db import Db
from .lib.logging import Logging
from .components.broker import Broker
from .lib.server import Server, http_response


class CodexBot:

    # Make decorator for HTTP callback public
    http_response = http_response

    def __init__(self, application_name, host, port, db_config, token):
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

        self.user_answer_callback = None

        self.logging = self.init_logging()
        self.db = self.init_db(db_config)
        self.server = self.init_server()
        self.broker = self.init_broker(application_name, queue_name)

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

    def set_user_answer_callback(self, callback):
        self.user_answer_callback = callback

    async def send_to_chat(self, chat_hash, message):
        await self.broker.api.send('send to service', {
            "chat_hash": chat_hash,
            "text": message
        })

    async def send_image_to_chat(self, chat_hash, photo, caption=None):
        await self.broker.api.send('send to service', {
            "chat_hash": chat_hash,
            "photo": photo,
            "caption": caption
        })


    async def wait_user_answer(self, user, chat, prompt=''):
        await self.broker.api.wait_user_answer(user, chat, prompt)

