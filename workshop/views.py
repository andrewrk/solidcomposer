from opensourcemusic.workshop.models import *
from opensourcemusic.main.models import *
from opensourcemusic.main.views import safe_model_to_dict, json_response

def ajax_home(request):
    data = {
        'user': {
            'is_authenticated': request.user.is_authenticated(),
        },
    }

    return json_response(data)
