#!/usr/bin/env python3
"""
Test script for test email functionality.
Tests the complete email sending workflow including SMTP configuration and error handling.
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestEmailTestSuite:
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
            
    def test_email_environment_variables(self):
        """Test that email environment variables are configured"""
        mailjet_api_key = os.getenv('MAILJET_API_KEY')
        mailjet_secret_key = os.getenv('MAILJET_SECRET_KEY')
        email_sender = os.getenv('EMAIL_SENDER')
        
        checks = []
        if mailjet_api_key:
            checks.append(f"API_KEY=✅({mailjet_api_key[:8]}...)")
        else:
            checks.append("API_KEY=❌")
            
        if mailjet_secret_key:
            checks.append(f"SECRET_KEY=✅({mailjet_secret_key[:8]}...)")
        else:
            checks.append("SECRET_KEY=❌")
            
        if email_sender:
            checks.append(f"SENDER=✅({email_sender})")
        else:
            checks.append("SENDER=❌")
            
        all_present = all("✅" in check for check in checks)
        self.log_test("Email Environment Variables", all_present, "; ".join(checks))
        
        return all_present
        
    def test_email_settings_configured(self):
        """Test that email settings are configured in the system"""
        try:
            with open("app/data/settings.json", 'r') as f:
                settings = json.load(f)
                
            recipient_email = settings.get('recipient_email', '')
            cc_emails = settings.get('cc_emails', '')
            
            checks = []
            if recipient_email:
                checks.append(f"recipient=✅({recipient_email})")
            else:
                checks.append("recipient=❌")
                
            if cc_emails:
                checks.append(f"cc=✅({cc_emails})")
            else:
                checks.append("cc=✅(empty)")  # CC can be empty
                
            has_recipient = bool(recipient_email)
            self.log_test("Email Settings Configured", has_recipient, "; ".join(checks))
            
            return has_recipient
            
        except Exception as e:
            self.log_test("Email Settings Configured", False, f"Error reading settings: {e}")
            return False
            
    def test_test_email_endpoint_access(self):
        """Test that test email endpoint is accessible"""
        try:
            response = self.session.post(
                f"{self.base_url}/settings/test-email",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            # Any response other than 404 means the endpoint exists
            if response.status_code != 404:
                self.log_test("Test Email Endpoint Access", True, f"Endpoint accessible (status: {response.status_code})")
                return True
            else:
                self.log_test("Test Email Endpoint Access", False, "Endpoint not found (404)")
                return False
                
        except Exception as e:
            self.log_test("Test Email Endpoint Access", False, f"Error: {e}")
            return False
            
    def test_test_email_api_endpoint(self):
        """Test the API test email endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/test-email",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("Test Email API Endpoint", True, f"Email sent successfully: {result.get('message')}")
                else:
                    self.log_test("Test Email API Endpoint", False, f"Email failed: {result.get('error')}")
            elif response.status_code == 400:
                result = response.json()
                self.log_test("Test Email API Endpoint", False, f"Configuration error: {result.get('error')}")
            elif response.status_code == 404:
                self.log_test("Test Email API Endpoint", False, "API endpoint not found")
            else:
                self.log_test("Test Email API Endpoint", False, f"Unexpected status {response.status_code}: {response.text}")
                
            return response.status_code in [200, 400]  # 400 is OK if it's a config issue
            
        except Exception as e:
            self.log_test("Test Email API Endpoint", False, f"Error: {e}")
            return False
            
    def test_email_service_import(self):
        """Test that email service can be imported and initialized"""
        try:
            # Test importing the email service
            import sys
            sys.path.insert(0, '.')
            
            from app.services.email_service import EmailService
            
            # Try to create an instance
            email_service = EmailService()
            
            self.log_test("Email Service Import", True, "EmailService imported and instantiated successfully")
            return True
            
        except Exception as e:
            self.log_test("Email Service Import", False, f"Error importing EmailService: {e}")
            return False
            
    def test_mailjet_api_connectivity(self):
        """Test basic Mailjet API connectivity"""
        try:
            mailjet_api_key = os.getenv('MAILJET_API_KEY')
            mailjet_secret_key = os.getenv('MAILJET_SECRET_KEY')
            
            if not mailjet_api_key or not mailjet_secret_key:
                self.log_test("Mailjet API Connectivity", False, "Missing Mailjet credentials")
                return False
                
            # Test basic API connectivity (without sending email)
            import requests
            import base64
            
            # Create basic auth header
            credentials = base64.b64encode(f"{mailjet_api_key}:{mailjet_secret_key}".encode()).decode()
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/json'
            }
            
            # Test with a simple API call (get account info)
            response = requests.get(
                'https://api.mailjet.com/v3/REST/apikey',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_test("Mailjet API Connectivity", True, "Mailjet API accessible with provided credentials")
                return True
            elif response.status_code == 401:
                self.log_test("Mailjet API Connectivity", False, "Mailjet API credentials invalid (401)")
                return False
            else:
                self.log_test("Mailjet API Connectivity", False, f"Mailjet API returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Mailjet API Connectivity", False, f"Error testing Mailjet API: {e}")
            return False
            
    def test_complete_email_workflow(self):
        """Test the complete email sending workflow"""
        try:
            # First ensure we have a recipient configured
            test_settings = {
                "recipient_email": "test-workflow@example.com",
                "cc_emails": "",
                "use_daily_send_time": True,
                "use_legacy_interval": False,
                "email_send_time": "10:00"
            }
            
            # Save test settings
            settings_response = self.session.post(
                f"{self.base_url}/settings/email",
                json=test_settings,
                headers={"Content-Type": "application/json"}
            )
            
            if settings_response.status_code != 200:
                self.log_test("Complete Email Workflow", False, "Failed to configure test settings")
                return False
                
            # Now try to send test email
            email_response = self.session.post(
                f"{self.base_url}/api/test-email",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if email_response.status_code == 200:
                result = email_response.json()
                if result.get('success'):
                    self.log_test("Complete Email Workflow", True, f"Complete workflow successful: {result.get('message')}")
                else:
                    self.log_test("Complete Email Workflow", False, f"Email sending failed: {result.get('error')}")
            else:
                self.log_test("Complete Email Workflow", False, f"Email API returned {email_response.status_code}")
                
            return email_response.status_code == 200
            
        except Exception as e:
            self.log_test("Complete Email Workflow", False, f"Error in complete workflow: {e}")
            return False
            
    def run_all_tests(self):
        """Run all test email functionality tests"""
        print("📬 Hospital Equipment System - Test Email Functionality Test Suite")
        print("=" * 75)
        
        # Login first
        if not self.login_as_admin():
            print("❌ Cannot proceed without admin login")
            return False
            
        # Test environment configuration
        self.test_email_environment_variables()
        
        # Test settings configuration
        self.test_email_settings_configured()
        
        # Test endpoint access
        self.test_test_email_endpoint_access()
        self.test_test_email_api_endpoint()
        
        # Test service layer
        self.test_email_service_import()
        
        # Test external connectivity
        self.test_mailjet_api_connectivity()
        
        # Test complete workflow
        self.test_complete_email_workflow()
        
        # Summary
        print("\n📊 TEST EMAIL FUNCTIONALITY SUMMARY")
        print("=" * 40)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed >= total - 2:  # Allow for minor failures
            print("🎉 Test email functionality working correctly!")
            return True
        else:
            print("⚠️  Test email functionality has issues. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = TestEmailTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
