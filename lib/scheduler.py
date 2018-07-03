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
            self.sdk.scheduler.restore(say_hello)

        :param processor: function, which returns appropriate callback to call for the job (by payload)
        """
        # Get jobs from db
        jobs = self.sdk.db.find(Scheduler.COLLECTION_NAME, {})

        # Run jobs
        for job in jobs:
            self.scheduler.add_job(
                processor,
                id=job['id'],
                args=job['args'],
                trigger='cron',
                replace_existing=True,
                **job['trigger_params']
            )

    def add(self, callback, payload, args, trigger_params=None):
        """
        Add new scheduling job.
            - Append params to DB
            - Add Apscheduler job

        Example:
            def say_hello(payload, data):
                print(data['message'])

            self.sdk.scheduler.add(
                say_hello,                                      # Callback function
                payload,                                        # Job identify by chat and bot
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
        :param payload: chat and bot
        :param args: arguments for callback function
        :param trigger_params: {'minute': '*', 'hour': '*/2'}
        """
        job_id = self.__create_id(payload)

        try:
            # Save job to db
            self.sdk.db.insert(
                Scheduler.COLLECTION_NAME,
                {
                    'id': job_id,
                    'trigger_params': trigger_params,
                    'args': args
                }
            )

            # Run job
            self.scheduler.add_job(
                callback,
                id=job_id,
                args=args,
                trigger='cron',
                replace_existing=True,
                **trigger_params
            )
        except Exception as e:
            if self.sdk.hawk:
                self.sdk.hawk.catch()
            self.sdk.logging.debug("Error: {}".format(e))

    def find(self, payload):
        """
        Return saved scheduler data from DB by chat_id
        :param payload: chat and bot
        :return: data from db
        """
        job_id = self.__create_id(payload)

        result = self.sdk.db.find_one(Scheduler.COLLECTION_NAME, {'id': job_id})

        return result

    def remove(self, payload):
        """
        Remove saved scheduler data from DB and stop job by chat_id

        Example:
            self.sdk.scheduler.remove(
                payload                    # Job identifier by chat and bot
            )

        :param payload: chat and bot
        :return: remove result
        """
        job_id = self.__create_id(payload)

        try:
            self.scheduler.remove_job(job_id)
        except Exception as e:
            if self.sdk.hawk:
                self.sdk.hawk.catch()
            self.sdk.logging.debug("Error during remove job: {}".format(e))

        return self.sdk.db.remove(Scheduler.COLLECTION_NAME, {'id': job_id})

    def __create_id(self, payload):
        job_id = payload.get('chat')

        bot_hash = payload.get('bot', None)

        if bot_hash:
            job_id = "{}:{}".format(bot_hash, job_id)

        return job_id
