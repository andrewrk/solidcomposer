from django_extensions.management.jobs import DailyJob
from main.models import Profile
from main import payment
from django.conf import settings

from datetime import datetime, timedelta

class Job(DailyJob):
    "bills recurring-payment customers"
    help = __doc__

    def execute(self):
        # get accounts that need to be billed
        now = datetime.now()
        profiles = Profile.objects.filter(account_expire_date__lte=now)
        # GIMME TEH MONIES!
        for profile in profiles:
            payment.bill_user(profile.user)

        # downgrade accounts that are a week behind payment to free
        # TODO: this is commented out because we don't want accidents to happen.
        # the way it should work is that a report is made of people whose accounts
        # we could not bill, and we contact those people to tell them we'll have to 
        # revert them to free if they don't pay.
        #profiles = Profile.objects.filter(account_expire_date__lte=now-timedelta(days=7))
        #for profile in profiles:
        #    downgrade_account_to_free(profile.user)
