class RemoveWWW():
    def process_request(self, request):
        try:
            if request.META['HTTP_HOST'].lower()[:4] == 'www.':
                from django.http import HttpResponsePermanentRedirect
                return HttpResponsePermanentRedirect(request.build_absolute_uri().replace('//www.', '//'))
        except:
            pass
        return None


