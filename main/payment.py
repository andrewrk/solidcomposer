import fpys
from django.conf import settings
from main.models import Transaction
import sys

FAILED, SUCCESS, NO_PIPELINE, INVALID_SIGNATURE = range(4)

def _get_client():
    if settings.DEBUG:
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
                return (FAILED, None)

            transaction.token_id = request.GET.get('tokenID')
            transaction.expiry = request.GET.get('expiry', '')
            transaction.save()

            return (SUCCESS, transaction)
        else:
            return (FAILED, None)
    else:
        return (INVALID_SIGNATURE, None)
