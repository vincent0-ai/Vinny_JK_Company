import json
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from api.models import Order, Payment, Product, Category
from api.utils import MpesaClient

class MpesaIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Test Category")
        self.product = Product.objects.create(
            name="Test Product",
            price=10.00,
            stock_quantity=10,
            category=self.category
        )
        self.order = Order.objects.create(
            total_price=10.00,
            full_name="John Doe",
            phone_number="254700000000"
        )

    @patch('api.utils.MpesaClient.stk_push')
    def test_initiate_mpesa_payment(self, mock_stk_push):
        # Mock success response from Daraja
        mock_stk_push.return_value = {
            'ResponseCode': '0',
            'CheckoutRequestID': 'ws_CO_12345',
            'CustomerMessage': 'STK Push initiated'
        }

        url = f'/api/payment/mpesa/initiate/{self.order.id}/'
        response = self.client.post(url, {'phone_number': '0115709680'}, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.first()
        self.assertEqual(payment.status, 'Pending')
        self.assertEqual(payment.transaction_id, 'ws_CO_12345')

    def test_mpesa_callback_success(self):
        # Create a pending payment
        payment = Payment.objects.create(
            order=self.order,
            transaction_id='ws_CO_12345',
            payment_method='M-Pesa',
            amount=10.00,
            status='Pending'
        )

        callback_data = {
            "Body": {
                "stkCallback": {
                    "MerchantRequestID": "29115-3462051-1",
                    "CheckoutRequestID": "ws_CO_12345",
                    "ResultCode": 0,
                    "ResultDesc": "The service request is processed successfully.",
                    "CallbackMetadata": {
                        "Item": [
                            {"Name": "Amount", "Value": 10.00},
                            {"Name": "MpesaReceiptNumber", "Value": "NLJ7RT6SYZ"},
                            {"Name": "TransactionDate", "Value": 20240101120000},
                            {"Name": "PhoneNumber", "Value": 254700000000}
                        ]
                    }
                }
            }
        }

        url = '/api/payment/mpesa/callback/'
        response = self.client.post(url, json.dumps(callback_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Completed')
        self.assertEqual(payment.mpesa_receipt_number, 'NLJ7RT6SYZ')
        
        self.order.refresh_from_db()
        self.assertTrue(self.order.is_paid)

    def test_mpesa_callback_failure(self):
        payment = Payment.objects.create(
            order=self.order,
            transaction_id='ws_CO_12345',
            payment_method='M-Pesa',
            amount=10.00,
            status='Pending'
        )

        callback_data = {
            "Body": {
                "stkCallback": {
                    "CheckoutRequestID": "ws_CO_12345",
                    "ResultCode": 1032,
                    "ResultDesc": "Request cancelled by user"
                }
            }
        }

        url = '/api/payment/mpesa/callback/'
        response = self.client.post(url, json.dumps(callback_data), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'Failed')
        self.order.refresh_from_db()
        self.assertFalse(self.order.is_paid)
