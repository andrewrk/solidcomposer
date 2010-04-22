from django.template import RequestContext
from opensourcemusic.main.models import Profile

import datetime

def global_values(request):
    recent_time = datetime.datetime.today() - datetime.timedelta(minutes=10)
    online_profiles = Profile.objects.filter(date_activity__gte=recent_time)
    user = request.user
    request_url = request.get_full_path()
    server_time = datetime.datetime.today().strftime('%B %d, %Y %H:%M:%S')

    return locals()

