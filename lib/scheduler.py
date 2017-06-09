from apscheduler.schedulers.asyncio import AsyncIOScheduler


class Scheduler:

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
