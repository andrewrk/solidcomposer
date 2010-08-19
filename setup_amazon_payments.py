#!/usr/bin/python

# set django environment
from django.core.management import setup_environ
import settings
setup_environ(settings)

import fpys

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

client = _get_client()

recipient_response = client.installPaymentInstruction(
    payment_instruction="MyRole == 'Recipient' orSay 'Role does not match';",
    caller_reference="recipient_instruction",
    token_type="Unrestricted",
    token_friendly_name="Recipient payment instruction"
)

caller_response = client.installPaymentInstruction(
    payment_instruction="MyRole == 'Caller' orSay 'Role does not match';",
    caller_reference="caller_instruction",
    token_type="Unrestricted",
    token_friendly_name="Caller payment instruction"
)

if recipient_response.success and caller_response.success:
    print("AWS_RECIPIENT_INSTRUCTION_TOKEN_ID = '{0}'".format(recipient_response.tokenId))
    print("AWS_RECIPIENT_INSTRUCTION_REQUEST_ID = '{0}'".format(recipient_response.requestId))
    print("AWS_CALLER_INSTRUCTION_TOKEN_ID = '{0}'".format(caller_response.tokenId))
    print("AWS_CALLER_INSTRUCTION_REQUEST_ID = '{0}'".format(caller_response.requestId))
else:
    print("recipient response: " + recipient_response.status)
    print("caller response: " + caller_response.status)
