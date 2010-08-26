from django.conf import settings

def ssl_media(request):
    """
    changes MEDIA_URL to https if using SSL connection
    """
    media_url = settings.MEDIA_URL
    parts = media_url.split(':')

    if request.is_secure():
        protocol = 'https'
    else:
        protocol = 'http'

    new_media_url = protocol + ":" + ":".join(parts[1:])
    return {'MEDIA_URL': new_media_url}
