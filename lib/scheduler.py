from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:

    COLLECTION_NAME = 'application_schedules'

    def __init__(self, sdk):
        """
        Initialize apscheduler and start
        :param sdk:
        """
        self.sdk = sdk
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    def restore(self, processor):
        """
        Restore jobs from DB.
            - Get all jobs
            - Get callback, returned by processor function by payload
            - Run scheduler job
        :param processor: function, which returns appropriate callback to call for the job (by payload)
        """
        jobs = self.sdk.db.find(Scheduler.COLLECTION_NAME, {})
        for job in jobs:
            self.scheduler.add_job(processor(job.get('payload', None)),
                                   id=job['chat_id'],
                                   hour=22,
                                   minute=45,
                                   args=job['args'],
                                   trigger='cron',
                                   replace_existing=True)

    def add(self, callback, chat_id, args, hour, payload=None):
        """
        Add new scheduling job.
            - Append params to DB
            - Add Apscheduler job
        :param callback: function to execute at the time
        :param chat_id: chat ID
        :param args: arguments for callback function
        :param hour: time to run in HH:mm format
        :param payload: data to keep in DB for the further restore function usage
        """
        try:
            self.sdk.db.insert(Scheduler.COLLECTION_NAME, {'chat_id': chat_id,
                                                           'hour': hour,
                                                           'args': args,
                                                           'payload': payload,
                                                           })
            self.scheduler.add_job(callback,
                                   id=chat_id,
                                   hour=hour,
                                   minute=51,
                                   args=args,
                                   trigger='cron',
                                   replace_existing=True)
        except Exception as e:
            self.sdk.logging.debug("Error: {}".format(e))

    def find(self, chat_id):
        """
        Return saved scheduler data from DB by chat_id
        :param chat_id: chat ID
        :return: data from db
        """
        result = self.sdk.db.find_one(Scheduler.COLLECTION_NAME, {'chat_id': chat_id})
        return result

    def remove(self, chat_id):
        """
        Remove saved scheduler data from DB and stop job by chat_id
        :param chat_id: chat ID
        :return: remove result
        """
        try:
            self.scheduler.remove_job(chat_id)
        except Exception as e:
            self.sdk.logging.debug("Error during remove job: {}".format(e))
        return self.sdk.db.remove(Scheduler.COLLECTION_NAME, {'chat_id': chat_id})
