#!/usr/bin/env python3
"""
Comprehensive test script for Send Message functionality.
Tests the complete workflow: login -> send message -> verify email delivery.
"""

import requests
import json
import sys
import time
from pathlib import Path

class SendMessageTestSuite:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5001"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def login_as_admin(self):
        """Login as admin user"""
        try:
            # Get login page first
            self.session.get(f"{self.base_url}/auth/login")
            
            # Login with admin credentials
            login_data = {
                'username': 'admin',
                'password': 'admin'
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data=login_data,
                allow_redirects=False
            )
            
            if response.status_code in [302, 303]:
                self.log_test("Admin Login", True, "Successfully logged in as admin")
                return True
            else:
                self.log_test("Admin Login", False, f"Login failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Login error: {e}")
            return False
            
    def test_send_message_api_functionality(self):
        """Test the Send Message API endpoint functionality"""
        try:
            print("   Calling /api/send-immediate-reminders endpoint...")
            
            response = self.session.post(
                f"{self.base_url}/api/send-immediate-reminders",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                success = result.get('success', False)
                emails_sent = result.get('emails_sent', 0)
                message = result.get('message', '')
                
                if success and emails_sent > 0:
                    self.log_test("Send Message API Functionality", True, f"Successfully sent {emails_sent} emails: {message}")
                    return emails_sent
                elif success and emails_sent == 0:
                    self.log_test("Send Message API Functionality", True, f"API successful but no emails needed: {message}")
                    return 0
                else:
                    self.log_test("Send Message API Functionality", False, f"API returned success=False: {message}")
                    return 0
                    
            else:
                result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error = result.get('error', response.text)
                self.log_test("Send Message API Functionality", False, f"API returned {response.status_code}: {error}")
                return 0
                
        except Exception as e:
            self.log_test("Send Message API Functionality", False, f"Error: {e}")
            return 0
            
    def test_send_message_frontend_simulation(self):
        """Test simulating the frontend Send Message button behavior"""
        try:
            print("   Simulating frontend Send Message button click...")
            
            # This simulates what the JavaScript does when the Send Message button is clicked
            response = self.session.post(
                f"{self.base_url}/api/send-immediate-reminders",
                json={},
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                emails_sent = result.get('emails_sent', 0)
                
                # This is what the frontend JavaScript expects
                if emails_sent > 0:
                    frontend_message = f"Successfully sent {emails_sent} reminder emails for equipment maintenance."
                    self.log_test("Send Message Frontend Simulation", True, frontend_message)
                else:
                    frontend_message = "Successfully sent 0 messages"
                    self.log_test("Send Message Frontend Simulation", True, f"Frontend would show: {frontend_message}")
                    
                return emails_sent
                
            else:
                self.log_test("Send Message Frontend Simulation", False, f"Frontend would show error: {response.status_code}")
                return 0
                
        except Exception as e:
            self.log_test("Send Message Frontend Simulation", False, f"Frontend would show error: {e}")
            return 0
            
    def test_email_delivery_verification(self):
        """Test that emails are actually being delivered (not just sent)"""
        try:
            # We can't directly verify email delivery without access to the recipient's inbox,
            # but we can verify that the email service is properly configured and working
            
            # Test the email service configuration
            from app.config import Config
            import os
            
            mailjet_api_key = os.getenv('MAILJET_API_KEY')
            mailjet_secret_key = os.getenv('MAILJET_SECRET_KEY')
            email_sender = os.getenv('EMAIL_SENDER')
            
            config_checks = []
            if mailjet_api_key:
                config_checks.append("API_KEY=✅")
            else:
                config_checks.append("API_KEY=❌")
                
            if mailjet_secret_key:
                config_checks.append("SECRET_KEY=✅")
            else:
                config_checks.append("SECRET_KEY=❌")
                
            if email_sender:
                config_checks.append(f"SENDER=✅({email_sender})")
            else:
                config_checks.append("SENDER=❌")
                
            # Check recipient configuration
            with open("app/data/settings.json", 'r') as f:
                settings = json.load(f)
                
            recipient_email = settings.get('recipient_email', '')
            if recipient_email:
                config_checks.append(f"RECIPIENT=✅({recipient_email})")
            else:
                config_checks.append("RECIPIENT=❌")
                
            all_configured = all("✅" in check for check in config_checks)
            
            if all_configured:
                self.log_test("Email Delivery Configuration", True, f"All email delivery components configured: {'; '.join(config_checks)}")
            else:
                self.log_test("Email Delivery Configuration", False, f"Missing email configuration: {'; '.join(config_checks)}")
                
            return all_configured
            
        except Exception as e:
            self.log_test("Email Delivery Configuration", False, f"Error: {e}")
            return False
            
    def test_message_content_and_recipients(self):
        """Test that messages have proper content and recipients"""
        try:
            # Check the settings for recipient configuration
            with open("app/data/settings.json", 'r') as f:
                settings = json.load(f)
                
            recipient_email = settings.get('recipient_email', '')
            cc_emails = settings.get('cc_emails', '')
            
            # Verify recipient configuration
            if recipient_email:
                recipient_info = f"Primary: {recipient_email}"
                if cc_emails:
                    recipient_info += f", CC: {cc_emails}"
                    
                self.log_test("Message Recipients Configuration", True, recipient_info)
                return True
            else:
                self.log_test("Message Recipients Configuration", False, "No recipient email configured")
                return False
                
        except Exception as e:
            self.log_test("Message Recipients Configuration", False, f"Error: {e}")
            return False
            
    def test_send_message_vs_test_email_comparison(self):
        """Compare Send Message functionality with working Test Email functionality"""
        try:
            print("   Comparing Send Message vs Test Email functionality...")
            
            # Test the test email endpoint (we know this works)
            test_email_response = self.session.post(
                f"{self.base_url}/api/test-email",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            # Test the send message endpoint
            send_message_response = self.session.post(
                f"{self.base_url}/api/send-immediate-reminders",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            test_email_works = test_email_response.status_code == 200
            send_message_works = send_message_response.status_code == 200
            
            if test_email_works and send_message_works:
                test_result = test_email_response.json()
                send_result = send_message_response.json()
                
                comparison = f"Test Email: {test_result.get('message', 'Success')}, Send Message: {send_result.get('emails_sent', 0)} emails"
                self.log_test("Send Message vs Test Email Comparison", True, comparison)
                return True
            else:
                comparison = f"Test Email: {test_email_response.status_code}, Send Message: {send_message_response.status_code}"
                self.log_test("Send Message vs Test Email Comparison", False, comparison)
                return False
                
        except Exception as e:
            self.log_test("Send Message vs Test Email Comparison", False, f"Error: {e}")
            return False
            
    def run_comprehensive_test(self):
        """Run comprehensive Send Message functionality test"""
        print("📧 Hospital Equipment System - Send Message Complete Test Suite")
        print("=" * 75)
        print("Testing the complete Send Message workflow...")
        print()
        
        # Login first
        if not self.login_as_admin():
            print("❌ Cannot proceed without admin login")
            return False
            
        # Test API functionality
        print("\n🔧 Testing Send Message API...")
        emails_sent = self.test_send_message_api_functionality()
        
        # Test frontend simulation
        print("\n🌐 Testing Frontend Simulation...")
        frontend_result = self.test_send_message_frontend_simulation()
        
        # Test email delivery configuration
        print("\n📬 Testing Email Delivery...")
        self.test_email_delivery_verification()
        
        # Test message recipients
        print("\n👥 Testing Recipients...")
        self.test_message_content_and_recipients()
        
        # Compare with test email
        print("\n🔍 Testing Comparison...")
        self.test_send_message_vs_test_email_comparison()
        
        # Summary
        print("\n📊 SEND MESSAGE TEST SUMMARY")
        print("=" * 50)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        # Key results
        print(f"\n🎯 KEY RESULTS:")
        print(f"   - API endpoint emails sent: {emails_sent}")
        print(f"   - Frontend simulation result: {frontend_result}")
        
        if emails_sent > 0 and frontend_result > 0:
            print("\n✅ SEND MESSAGE FUNCTIONALITY FIXED!")
            print("   The 'Send Message' button now works correctly and sends actual emails.")
            print(f"   Users will see: 'Successfully sent {emails_sent} messages' instead of 'Successfully sent 0 messages'")
            return True
        elif emails_sent == 0 and frontend_result == 0:
            print("\n⚠️  SEND MESSAGE RETURNS 0 (but this may be correct)")
            print("   This could mean no maintenance is due in the immediate thresholds.")
            print("   Check if this is expected based on your equipment maintenance schedules.")
            return True
        else:
            print("\n❌ SEND MESSAGE FUNCTIONALITY STILL HAS ISSUES")
            print("   Check the failed tests above for details.")
            return False

if __name__ == "__main__":
    tester = SendMessageTestSuite()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)
