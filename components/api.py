import json
import logging

from ..lib.logging import Logging


class API:

    def __init__(self, broker, app_name, hawk):

        self.hawk = hawk
        self.app_name = app_name
        self.broker = broker
        self.token = app_name
        self.db = broker.core.db
        self.logging = Logging()
        self.commands_list = {}

        # Methods list (command => processor)
        self.methods = {
            'show message': self.show_message,
            'service callback': self.service_callback,
            'user answer': self.user_answer,
            'callback query': self.callback_query
        }

    async def process(self, message_data):
        try:
            message_data = json.loads(message_data)
            payload = message_data['payload']
            command = message_data.get('command', 'show message')
            await self.methods[command](payload)
        except Exception as e:
            if self.hawk:
                self.hawk.catch()
            logging.error("API Message Process error: {}".format(e))

    async def send(self, command, payload):

        data = json.dumps({'token': self.broker.core.token,
                           'command': command,
                           'payload': payload})
        await self.broker.send(data)

    async def register_commands(self, commands):
        commands_to_send = []
        for cmd, desc, clb in commands:
            self.commands_list[cmd] = clb
            commands_to_send.append((cmd, desc))
        await self.send('register commands', commands_to_send)

    # API COMMANDS

    async def show_message(self, data):
        logging.info(data)

    async def service_callback(self, data):
        await self.commands_list[data['command']](data)

    async def user_answer(self, data):
        if self.broker.core.user_answer_handler:
            await self.broker.core.user_answer_handler(data)

    async def wait_user_answer(self, user, chat, prompt='', bot=None):
        await self.send('wait user answer', {'user': user, 'chat': chat, 'prompt': prompt, 'bot': bot})

    async def callback_query(self, data):
        if self.broker.core.callback_query_handler:
            await self.broker.core.callback_query_handler(data)
