import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vinny_kj.settings')
django.setup()

def test_email():
    print("--- SMTP Connection Test ---")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    
    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        print("\nERROR: EMAIL_HOST_USER or EMAIL_HOST_PASSWORD not set in .env file.")
        return

    subject = "SMTP Test Connection - VIN-KJ Auto Services"
    message = "This is a test email to verify that your SMTP settings are correctly configured."
    recipient = settings.EMAIL_HOST_USER # Send to self for testing
    
    try:
        print(f"\nAttempting to send test email to {recipient}...")
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        print("\nSUCCESS: Email sent successfully! Please check your inbox.")
    except Exception as e:
        print(f"\nFAILED: Could not send email.")
        print(f"Error: {e}")
        if "Authentication failed" in str(e) or "SMTPAuthenticationError" in str(e):
            print("\nTIP: If you're using Gmail, make sure you use an 'App Password'.")

if __name__ == "__main__":
    test_email()
