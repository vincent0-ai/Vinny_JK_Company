import requests
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

import logging

logger = logging.getLogger(__name__)

class MpesaClient:
    def __init__(self):
        self.access_token = None
        self.token_expiry = None

    def get_access_token(self):
        # In production, you might want to cache this in Redis or database
        consumer_key = str(settings.DARAJA_CONSUMER_KEY).strip()
        consumer_secret = str(settings.DARAJA_CONSUMER_SECRET).strip()
        api_url = f"{str(settings.DARAJA_BASE_URL).strip()}/oauth/v1/generate?grant_type=client_credentials"

        try:
            r = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
            r.raise_for_status()
            token = r.json()['access_token']
            logger.info("M-Pesa Access Token generated successfully")
            return token
        except Exception as e:
            logger.error(f"Error generating M-Pesa access token: {e}")
            return None

    def stk_push(self, phone_number, amount, account_reference, transaction_desc="Payment"):
        access_token = self.get_access_token()
        if not access_token:
            logger.error("Failed to get M-Pesa access token for STK push")
            return None

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        business_short_code = settings.DARAJA_BUSINESS_SHORTCODE
        passkey = settings.DARAJA_PASSKEY
        
        if not business_short_code or not passkey:
            logger.error("DARAJA_BUSINESS_SHORTCODE or DARAJA_PASSKEY not set in settings")
            return None

        data_to_encode = business_short_code + passkey + timestamp
        password = base64.b64encode(data_to_encode.encode('utf-8')).decode('utf-8')

        # Daraja AccountReference must be max 12 chars and alphanumeric
        sanitized_account_ref = str(account_reference)[:12].replace(' ', '').replace('-', '')

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline", # Or CustomerBuyGoodsOnline
            "Amount": int(amount), 
            "PartyA": phone_number,
            "PartyB": business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": settings.DARAJA_CALLBACK_URL,
            "AccountReference": sanitized_account_ref,
            "TransactionDesc": transaction_desc[:20] 
        }

        logger.info(f"Initiating STK Push: {phone_number}, Amount: {amount}, Ref: {sanitized_account_ref}")

        api_url = f"{settings.DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"

        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response_data = response.json()
            logger.info(f"Daraja Response: {response.status_code} - {response_data.get('CustomerMessage')}")
            
            if response.status_code != 200:
                logger.error(f"Daraja Error: {response.text}")
            
            return response_data
        except Exception as e:
            logger.error(f"Error initiating STK push: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            return None

def send_receipt_email(to_email, subject, message_body):
    """ Helper function to send Email receipts """
    if not to_email:
        logger.warning("No email address provided for receipt notification")
        return False
    
    try:
        html_message = f'<div style="font-family: Arial, sans-serif; padding: 20px;"><h3>VINNY KJ</h3><p>{message_body}</p></div>'
        plain_message = strip_tags(html_message)
        from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@vinkj.com')
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Receipt Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email receipt to {to_email}: {e}")
        return False



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
