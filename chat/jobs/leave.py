from chat.models import Appearance, ChatMessage
from datetime import datetime, timedelta
from django.conf import settings
from django_extensions.management.jobs import BaseJob


class Job(BaseJob):
    """
    Cron Job that checks if any users should be considered as having left any
    ChatRooms and generates Leave Messages.

    Should be run every minute.
    """
    help = __doc__

    def execute(self):
        expire_date = datetime.now() - timedelta(seconds=settings.CHAT_TIMEOUT)
        appearances = Appearance.objects.filter(timestamp__lte=expire_date)
        
        for appearance in appearances:
            # generate leave messages in each room
            m = ChatMessage()
            m.room=appearance.room
            m.type=ChatMessage.LEAVE
            m.author=appearance.person
            m.save()

        appearances.delete()

