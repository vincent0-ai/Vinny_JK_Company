import os
import django
import sys
import requests
import json
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinny_kj.settings')
django.setup()

from api.models import Order, Product, Payment
from django.conf import settings

def print_header(text):
    print(f"\n{'='*50}")
    print(f" {text}")
    print(f"{'='*50}")

def create_test_order():
    print_header("Creating Test Order")
    product, _ = Product.objects.get_or_create(
        name="API Test Product",
        defaults={
            'price': 10.00, # Low price for testing
            'stock_quantity': 100,
            'description': 'Product for API testing',
            'slug': 'api-test-product'
        }
    )
    
    order = Order.objects.create(
        product=product,
        quantity=1,
        total_price=product.price,
        full_name="Tester",
        phone_number="0700000000"
    )
    print(f"Created Order ID: {order.id} | Amount: {order.total_price}")
    return order

def test_mpesa(order, base_url):
    print_header("Testing M-Pesa STK Push")
    
    phone = input("Enter M-Pesa Phone Number (e.g., 0712345678): ").strip()
    if not phone:
        print("Skipping M-Pesa test.")
        return

    url = f"{base_url}/api/payment/mpesa/initiate/{order.id}/"
    payload = {"phone_number": phone}
    
    print(f"Sending request to: {url}")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:", json.dumps(response.json(), indent=2))
        except:
            print("Response Text:", response.text)
            
        if response.status_code == 200:
            print("\n✅ STK Push Initiated successfully!")
            print("Check your phone for the PIN prompt.")
            print("Note: For the transaction to complete on the backend,")
            print("the Callback URL in settings.py must be reachable by Safaricom (e.g., using ngrok).")
        else:
            print("\n❌ STK Push Failed.")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Could not connect to {base_url}.")
        print("Make sure your Django server is running (python manage.py runserver).")

def test_stripe(order, base_url):
    print_header("Testing Stripe Payment Intent")
    
    url = f"{base_url}/api/payment/stripe/initiate/{order.id}/"
    
    print(f"Sending request to: {url}")
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:", json.dumps(response.json(), indent=2))
        except:
            print("Response Text:", response.text)

        if response.status_code == 200:
            data = response.json()
            if 'client_secret' in data:
                print("\n✅ Stripe Payment Intent created successfully!")
                print(f"Client Secret: {data['client_secret']}")
            else:
                print("\n⚠️ Response received but missing client_secret.")
        else:
            print("\n❌ Stripe Test Failed.")

    except requests.exceptions.ConnectionError:
         print(f"\n❌ Could not connect to {base_url}.")

def main():
    print("Manual Payment Testing Script")
    print("-----------------------------")
    
    # Check Settings
    print(f"DARAJA_CONSUMER_KEY: {settings.DARAJA_CONSUMER_KEY[:5]}...")
    print(f"DARAJA_SHORTCODE: {settings.DARAJA_BUSINESS_SHORTCODE}")
    print(f"STRIPE_KEY_SET: {'Yes' if settings.STRIPE_SECRET_KEY else 'No'}")
    
    domain = input("\nEnter your testing domain (default: http://127.0.0.1:8000): ").strip()
    if not domain:
        domain = "http://127.0.0.1:8000"
    
    order = create_test_order()
    
    while True:
        print("\nOptions:")
        print("1. Test M-Pesa STK Push")
        print("2. Test Stripe Payment Intent")
        print("3. Exit")
        
        choice = input("Select option: ")
        
        if choice == '1':
            test_mpesa(order, domain)
        elif choice == '2':
            test_stripe(order, domain)
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
