#!/usr/bin/env python3
"""
Fix email configuration to ensure emails are sent to correct recipients.
"""

import json
import requests
from datetime import datetime

BASE_URL = "http://localhost:5001"
APP_SETTINGS_FILE = "app/data/settings.json"

def fix_email_configuration():
    """Fix the email configuration to use correct recipient addresses"""
    print("🔧 Fixing Email Configuration")
    print("=" * 50)
    
    # Step 1: Authenticate
    print("\n🔐 Step 1: Authentication")
    session = requests.Session()
    
    try:
        # Get main page to establish session
        session.get(f"{BASE_URL}/")
        
        # Login with admin credentials
        login_data = {'username': 'admin', 'password': 'admin'}
        login_response = session.post(f"{BASE_URL}/auth/login", data=login_data)
        
        if login_response.status_code in [200, 302, 303]:
            print("✅ Authentication successful")
        else:
            print(f"❌ Authentication failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    # Step 2: Get current settings
    print("\n📋 Step 2: Check Current Settings")
    
    try:
        current_response = session.get(f"{BASE_URL}/api/settings")
        if current_response.status_code == 200:
            current_settings = current_response.json()
            current_recipient = current_settings.get('recipient_email', 'unknown')
            current_cc = current_settings.get('cc_emails', 'unknown')
            current_time = current_settings.get('email_send_time', 'unknown')
            
            print(f"📧 Current recipient: {current_recipient}")
            print(f"📧 Current CC: {current_cc}")
            print(f"⏰ Current send time: {current_time}")
        else:
            print(f"❌ Failed to get current settings: {current_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting current settings: {e}")
        return False
    
    # Step 3: Fix email configuration
    print("\n🔧 Step 3: Fix Email Configuration")
    
    # Correct email configuration
    correct_email_settings = {
        "recipient_email": "alorfbiomed@gmail.com",
        "cc_emails": "lolotam@gmail.com, dr.vet.waleedtam@gmail.com",
        "use_daily_send_time": True,
        "use_legacy_interval": False,
        "email_send_time": "16:45"  # Keep current time
    }
    
    try:
        # Send the corrected settings
        fix_response = session.post(
            f"{BASE_URL}/settings/email",
            json=correct_email_settings,
            headers={"Content-Type": "application/json"}
        )
        
        if fix_response.status_code == 200:
            print("✅ Email configuration fixed successfully")
            print(f"📧 Primary recipient: {correct_email_settings['recipient_email']}")
            print(f"📧 CC recipients: {correct_email_settings['cc_emails']}")
            print(f"⏰ Send time: {correct_email_settings['email_send_time']}")
        else:
            print(f"❌ Failed to fix configuration: {fix_response.status_code}")
            try:
                error_data = fix_response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {fix_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing configuration: {e}")
        return False
    
    # Step 4: Verify the fix
    print("\n✅ Step 4: Verify Configuration Fix")
    
    try:
        # Wait a moment for the save to complete
        import time
        time.sleep(1)
        
        # Check settings file directly
        with open(APP_SETTINGS_FILE, 'r') as f:
            file_settings = json.load(f)
        
        file_recipient = file_settings.get('recipient_email')
        file_cc = file_settings.get('cc_emails')
        file_time = file_settings.get('email_send_time')
        
        print(f"📧 File recipient: {file_recipient}")
        print(f"📧 File CC: {file_cc}")
        print(f"⏰ File send time: {file_time}")
        
        # Verify via API
        verify_response = session.get(f"{BASE_URL}/api/settings")
        if verify_response.status_code == 200:
            api_settings = verify_response.json()
            api_recipient = api_settings.get('recipient_email')
            api_cc = api_settings.get('cc_emails')
            api_time = api_settings.get('email_send_time')
            
            print(f"📧 API recipient: {api_recipient}")
            print(f"📧 API CC: {api_cc}")
            print(f"⏰ API send time: {api_time}")
            
            # Check if everything is correct
            if (api_recipient == "alorfbiomed@gmail.com" and 
                "lolotam@gmail.com" in api_cc and 
                "dr.vet.waleedtam@gmail.com" in api_cc):
                print("\n🎉 EMAIL CONFIGURATION SUCCESSFULLY FIXED!")
                print("✅ All email addresses are now correct")
                print("✅ Emails will be sent to the right recipients")
                return True
            else:
                print("\n❌ Configuration still not correct")
                return False
        else:
            print(f"❌ API verification failed: {verify_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying fix: {e}")
        return False

def main():
    """Run the email configuration fix"""
    success = fix_email_configuration()
    
    if success:
        print("\n" + "=" * 70)
        print("📧 EMAIL CONFIGURATION FIXED SUCCESSFULLY!")
        print("=" * 70)
        print("✅ Primary recipient: alorfbiomed@gmail.com")
        print("✅ CC recipients: lolotam@gmail.com, dr.vet.waleedtam@gmail.com")
        print("✅ Send time: 16:45 (4:45 PM)")
        print("\n💡 NEXT STEPS:")
        print("1. Emails will now be sent to the correct addresses")
        print("2. Check your inboxes around 16:45 (4:45 PM) daily")
        print("3. Check spam/junk folders if emails don't appear in inbox")
        print("4. Use the Test Email feature to verify immediate delivery")
    else:
        print("\n❌ FAILED TO FIX EMAIL CONFIGURATION")
        print("Please check the error messages above and try again")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
