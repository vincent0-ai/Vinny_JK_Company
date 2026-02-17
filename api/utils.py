import requests
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime
from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class MpesaClient:
    def get_access_token(self):
        consumer_key = settings.DARAJA_CONSUMER_KEY
        consumer_secret = settings.DARAJA_CONSUMER_SECRET
        api_url = f"{settings.DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"

        try:
            r = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            r.raise_for_status()
            return r.json()['access_token']
        except Exception as e:
            print(f"Error generating access token: {e}")
            return None

    def stk_push(self, phone_number, amount, account_reference, transaction_desc="Payment"):
        access_token = self.get_access_token()
        if not access_token:
            return None

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        business_short_code = settings.DARAJA_BUSINESS_SHORTCODE
        passkey = settings.DARAJA_PASSKEY
        
        data_to_encode = business_short_code + passkey + timestamp
        password = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount), # Amount must be integer
            "PartyA": phone_number,
            "PartyB": business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.DARAJA_CALLBACK_URL,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        api_url = f"{settings.DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error initiating STK push: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response content: {e.response.content}")
            return None

def create_stripe_payment_intent(amount, currency='usd'):
    try:
        # Stripe expects amount in cents
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return intent
    except Exception as e:
        print(f"Error creating stripe payment intent: {e}")
        return None
