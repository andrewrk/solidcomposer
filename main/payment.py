import fpys
from django.conf import settings
from main.models import Transaction
import sys

from datetime import datetime, timedelta

FAILURE, SUCCESS, NO_PIPELINE, INVALID_SIGNATURE = range(4)

def _get_client():
    if settings.DEBUG or not settings.USE_AWS:
        fps_url = "https://fps.sandbox.amazonaws.com"
        pipeline_url = "https://authorize.payments-sandbox.amazon.com/cobranded-ui/actions/start"
    else:
        fps_url = "https://fps.amazonaws.com"
        pipeline_url = "https://authorize.payments.amazon.com/cobranded-ui/actions/start"
    return fpys.FlexiblePaymentClient(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        fps_url=fps_url,
        pipeline_url=pipeline_url)

def pipeline_url(user, next_url, plan):
    # create transaction record
    transaction = Transaction()
    transaction.user = user
    transaction.plan = plan
    transaction.amount = plan.usd_per_month
    transaction.save()

    client = _get_client()
    url = client.getPipelineUrl(
        caller_reference=str(transaction.id),
        payment_reason="{0} Account Monthly Fee".format(plan.title),
        transaction_amount=str(plan.usd_per_month),
        return_url=next_url,
        pipeline_name="Recurring",
        recurring_period="1 Month")
    return url

def process_pipeline_result(request):
    sig = request.GET.get('awsSignature', None)

    if sig is None:
        return (NO_PIPELINE, None)

    sig = sig.replace(" ", "+")

    client = _get_client()
    request_dict = dict([(key,val) for key, val in request.GET.iteritems()])
    valid = client.validate_pipeline_signature(sig, request.path+'?', request_dict)
    if valid:
        if request.GET.get('status') in ('SA', 'SB', 'SC'):
            transaction_id = request.GET.get('callerReference', 0)
            try:
                transaction = Transaction.objects.get(pk=int(transaction_id))
            except Transaction.DoesNotExist, ValueError:
                sys.stderr.write("Got transaction id {0} from amazon which we don't have in our records.".format(transaction_id))
                return (FAILURE, None)

            transaction.token_id = request.GET.get('tokenID')
            transaction.expiry = request.GET.get('expiry', '')
            transaction.save()

            return (SUCCESS, transaction)
        else:
            return (FAILURE, None)
    else:
        return (INVALID_SIGNATURE, None)

def bill_user(user):
    """
    if the user owes payment, this function will use amazon to bill them their
    monthly cost and add a month onto their account expire date
    """
    profile = user.get_profile()
    now = datetime.now()
    if profile.usd_per_month > 0 and profile.account_expire_date <= now:
        # hai amazon can we plz have their money?
        transaction = Transaction()
        transaction.plan = profile.plan
        transaction.token_id = profile.active_transaction.token_id
        transaction.amount = profile.usd_per_month
        transaction.user = user
        transaction.save()

        client = _get_client()
        response = client.pay(
            caller_token=settings.AWS_CALLER_INSTRUCTION_TOKEN_ID,
            sender_token=transaction.token_id,
            recipient_token=settings.AWS_RECIPIENT_INSTRUCTION_TOKEN_ID,
            amount=transaction.amount,
            caller_reference=str(transaction.id)
        )

        if not response.success:
            # TODO send of some kind of error email
            return

        transaction.request_id = response.requestId
        transaction.transaction_id = response.transaction.transactionId
        transaction.save()

        if response.transaction.status in ('Failure', 'Cancelled'):
            # TODO send some kind of error email
            return

        # give them the goods
        profile.account_expire_date += timedelta(days=31)
        profile.save()

