import logging

from aio_pika import IncomingMessage

from .api import API
from ..lib.rabbitmq import init_receiver, add_message_to_queue


class Broker:

    def __init__(self, core, event_loop, application_name, queue_name):
        """
        Application broker initialization
        :param core:
        :param event_loop:
        :param queue_name: - passed from sdk constructor
        """
        logging.info("Broker started with queue_name " + queue_name)
        self.core = core
        self.event_loop = event_loop
        self.queue_name = queue_name
        self.api = API(self, application_name)

    async def callback(self, message: IncomingMessage):
        with message.process():
            try:
                logging.debug(" [x] Received %r" % message.body)
                await self.api.process(message.body.decode("utf-8"))
            except Exception as e:
                logging.error("Broker callback error: {}".format(e))

    async def send(self, message, host='localhost'):

        await add_message_to_queue(
            message, 'core'
        )

    def start(self):
        self.event_loop.run_until_complete(init_receiver(self.callback, self.queue_name))
