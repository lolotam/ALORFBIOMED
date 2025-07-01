#!/usr/bin/env python3
"""
Direct test of the email service to identify issues.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_email_service_direct():
    """Test the email service directly"""
    print("🔧 Testing Email Service Directly")
    print("=" * 40)
    
    try:
        # Test environment variables
        mailjet_api_key = os.getenv('MAILJET_API_KEY')
        mailjet_secret_key = os.getenv('MAILJET_SECRET_KEY')
        email_sender = os.getenv('EMAIL_SENDER')
        
        print(f"✅ MAILJET_API_KEY: {mailjet_api_key[:8]}..." if mailjet_api_key else "❌ MAILJET_API_KEY: Not set")
        print(f"✅ MAILJET_SECRET_KEY: {mailjet_secret_key[:8]}..." if mailjet_secret_key else "❌ MAILJET_SECRET_KEY: Not set")
        print(f"✅ EMAIL_SENDER: {email_sender}" if email_sender else "❌ EMAIL_SENDER: Not set")
        
        if not all([mailjet_api_key, mailjet_secret_key, email_sender]):
            print("❌ Missing required environment variables")
            return False
            
        # Test importing the email service
        print("\n🔧 Testing EmailService Import...")
        from app.services.email_service import EmailService
        print("✅ EmailService imported successfully")
        
        # Test creating an instance
        email_service = EmailService()
        print("✅ EmailService instance created")
        
        # Test the static method directly
        print("\n🔧 Testing send_immediate_email method...")
        
        test_recipients = ["test@example.com"]
        test_subject = "Direct Test Email"
        test_body = """
        <h2>Direct Test Email</h2>
        <p>This is a direct test of the EmailService.send_immediate_email method.</p>
        <p>If you receive this, the email service is working correctly!</p>
        """
        
        print(f"Recipients: {test_recipients}")
        print(f"Subject: {test_subject}")
        print("Attempting to send email...")
        
        # Call the method
        result = EmailService.send_immediate_email(test_recipients, test_subject, test_body)
        
        if result:
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Email sending failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mailjet_direct():
    """Test Mailjet API directly"""
    print("\n🔧 Testing Mailjet API Directly")
    print("=" * 40)
    
    try:
        import requests
        import base64
        
        mailjet_api_key = os.getenv('MAILJET_API_KEY')
        mailjet_secret_key = os.getenv('MAILJET_SECRET_KEY')
        email_sender = os.getenv('EMAIL_SENDER')
        
        if not all([mailjet_api_key, mailjet_secret_key, email_sender]):
            print("❌ Missing Mailjet credentials")
            return False
            
        # Create basic auth header
        credentials = base64.b64encode(f"{mailjet_api_key}:{mailjet_secret_key}".encode()).decode()
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        # Test API connectivity
        print("Testing API connectivity...")
        response = requests.get(
            'https://api.mailjet.com/v3/REST/apikey',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Mailjet API connectivity successful")
            
            # Test sending a simple email
            print("Testing email sending...")
            email_data = {
                "Messages": [
                    {
                        "From": {
                            "Email": email_sender,
                            "Name": "Hospital Equipment System"
                        },
                        "To": [
                            {
                                "Email": "test@example.com",
                                "Name": "Test Recipient"
                            }
                        ],
                        "Subject": "Direct Mailjet API Test",
                        "HTMLPart": "<h3>This is a direct test of the Mailjet API</h3><p>If you receive this, the API is working!</p>"
                    }
                ]
            }
            
            send_response = requests.post(
                'https://api.mailjet.com/v3.1/send',
                headers=headers,
                json=email_data,
                timeout=30
            )
            
            print(f"Send response status: {send_response.status_code}")
            print(f"Send response: {send_response.text}")
            
            if send_response.status_code == 200:
                print("✅ Direct Mailjet email sending successful")
                return True
            else:
                print(f"❌ Direct Mailjet email sending failed: {send_response.status_code}")
                return False
                
        else:
            print(f"❌ Mailjet API connectivity failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Mailjet directly: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test config loading"""
    print("\n🔧 Testing Config Loading")
    print("=" * 40)
    
    try:
        from app.config import Config
        
        print(f"MAILJET_API_KEY: {'✅ Set' if Config.MAILJET_API_KEY else '❌ Not set'}")
        print(f"MAILJET_SECRET_KEY: {'✅ Set' if Config.MAILJET_SECRET_KEY else '❌ Not set'}")
        print(f"EMAIL_SENDER: {'✅ Set' if Config.EMAIL_SENDER else '❌ Not set'}")
        
        return all([Config.MAILJET_API_KEY, Config.MAILJET_SECRET_KEY, Config.EMAIL_SENDER])
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False

if __name__ == "__main__":
    print("📧 Hospital Equipment System - Direct Email Service Test")
    print("=" * 60)
    
    # Test config loading
    config_ok = test_config_loading()
    
    if config_ok:
        # Test email service
        service_ok = test_email_service_direct()
        
        # Test Mailjet directly
        mailjet_ok = test_mailjet_direct()
        
        print(f"\n📊 SUMMARY")
        print(f"Config Loading: {'✅' if config_ok else '❌'}")
        print(f"Email Service: {'✅' if service_ok else '❌'}")
        print(f"Mailjet Direct: {'✅' if mailjet_ok else '❌'}")
        
        if all([config_ok, service_ok, mailjet_ok]):
            print("🎉 All email tests passed!")
        else:
            print("⚠️  Some email tests failed")
    else:
        print("❌ Cannot proceed without proper config")
