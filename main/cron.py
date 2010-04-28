from django_cron import cronScheduler, Job

from datetime import datetime, timedelta
from opensourcemusic.main.models import *
from opensourcemusic.settings import CHAT_TIMEOUT

class CreateLeaveMessages(Job):
    """
    Cron Job that checks if any users should be considered as having left any
    ChatRooms and generates Leave Messages
    """

    # run every 20 seconds
    run_every = 20

    def job(self):
        expire_date = datetime.now() - timedelta(seconds=CHAT_TIMEOUT)
        appearances = Appearance.objects.filter(timestamp__lte=expire_date)

        for appearance in appearances:
            # generate leave messages in each room
            m = ChatMessage()
            m.room=appearance.room
            m.type=LEAVE
            m.author=appearance.person
            m.save()
            appearance.delete()

cronScheduler.register(CreateLeaveMessages)
