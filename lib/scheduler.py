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

        Example:
            self.sdk.scheduler.restore(Methods.say_hello)

        :param processor: function, which returns appropriate callback to call for the job (by payload)
        """
        # Get jobs from db
        jobs = self.sdk.db.find(Scheduler.COLLECTION_NAME, {})

        # Run jobs
        for job in jobs:
            self.scheduler.add_job(
                processor,
                id=job['chat_id'],
                args=job['args'],
                trigger='cron',
                replace_existing=True,
                **job['trigger_params']
            )

    def add(self, callback, chat_id, args, trigger_params=None, payload=None):
        """
        Add new scheduling job.
            - Append params to DB
            - Add Apscheduler job

        Example:
            self.sdk.scheduler.add(
                Methods.say_hello,                              # Callback function
                chat_id=payload["chat"],                        # Job identifier
                args=[payload, data],                           # Callback params
                trigger_params={'minute': '0', 'hour': '*/6'}   # Cron params
            )

        Available trigger_params:
            year (int|str) – 4-digit year
            month (int|str) – month (1-12)
            day (int|str) – day of the (1-31)
            week (int|str) – ISO week (1-53)
            day_of_week (int|str) – number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
            hour (int|str) – hour (0-23)
            minute (int|str) – minute (0-59)
            second (int|str) – second (0-59)

        :param callback: function to execute at the time
        :param chat_id: chat ID
        :param args: arguments for callback function
        :param trigger_params: {'minute': '*', 'hour': '*/2'}
        :param payload: data to keep in DB for the further restore function usage
        """
        try:
            # Save job to db
            self.sdk.db.insert(
                Scheduler.COLLECTION_NAME,
                {
                    'chat_id': chat_id,
                    'trigger_params': trigger_params,
                    'args': args,
                    'payload': payload,
                }
            )

            # Run job
            self.scheduler.add_job(
                callback,
                id=chat_id,
                args=args,
                trigger='cron',
                replace_existing=True,
                **trigger_params
            )
        except Exception as e:
            if self.sdk.hawk:
                self.sdk.hawk.catch()
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

        Example:
            self.sdk.scheduler.remove(
                payload['chat']             # Job identifier
            )

        :param chat_id: chat ID
        :return: remove result
        """
        try:
            self.scheduler.remove_job(chat_id)
        except Exception as e:
            if self.sdk.hawk:
                self.sdk.hawk.catch()
            self.sdk.logging.debug("Error during remove job: {}".format(e))

        return self.sdk.db.remove(Scheduler.COLLECTION_NAME, {'chat_id': chat_id})
