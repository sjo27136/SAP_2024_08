import os
from twilio.rest import Client

def send_sms(body):
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE_NUMBER')
    to_phone = os.getenv('TO_PHONE_NUMBER')

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=body,
        from_=from_phone,
        to=to_phone
    )
    print(f"SMS sent: {body}")
