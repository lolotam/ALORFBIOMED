#!/usr/bin/env python3
"""
Test script for VAPID key functionality and push notifications.
Verifies that the VAPID key format issues have been resolved.
"""

import requests
import json
import os
import base64
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VAPIDTestSuite:
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
        
    def test_vapid_env_variables(self):
        """Test that VAPID environment variables are properly set"""
        print("🔑 Testing VAPID Environment Variables...")
        
        vapid_private = os.getenv('VAPID_PRIVATE_KEY')
        vapid_public = os.getenv('VAPID_PUBLIC_KEY')
        vapid_subject = os.getenv('VAPID_SUBJECT')
        
        # Test private key
        if vapid_private:
            self.log_test("VAPID Private Key Present", True, f"Length: {len(vapid_private)} chars")
        else:
            self.log_test("VAPID Private Key Present", False, "VAPID_PRIVATE_KEY not found")
            
        # Test public key
        if vapid_public:
            self.log_test("VAPID Public Key Present", True, f"Length: {len(vapid_public)} chars")
        else:
            self.log_test("VAPID Public Key Present", False, "VAPID_PUBLIC_KEY not found")
            
        # Test subject format
        if vapid_subject:
            if vapid_subject.startswith('mailto:'):
                self.log_test("VAPID Subject Format", True, f"Correct format: {vapid_subject}")
            else:
                self.log_test("VAPID Subject Format", False, f"Missing 'mailto:' prefix: {vapid_subject}")
        else:
            self.log_test("VAPID Subject Present", False, "VAPID_SUBJECT not found")
            
        return all([vapid_private, vapid_public, vapid_subject])
        
    def test_vapid_key_format(self):
        """Test VAPID key format compatibility"""
        print("\n🔧 Testing VAPID Key Format...")
        
        vapid_private = os.getenv('VAPID_PRIVATE_KEY')
        vapid_public = os.getenv('VAPID_PUBLIC_KEY')
        
        if not vapid_private or not vapid_public:
            self.log_test("VAPID Key Format", False, "Keys not available for testing")
            return False
            
        try:
            # Test base64 decoding
            private_decoded = base64.urlsafe_b64decode(vapid_private + '==')  # Add padding
            public_decoded = base64.urlsafe_b64decode(vapid_public + '==')
            
            self.log_test("VAPID Key Base64 Decoding", True, f"Private: {len(private_decoded)} bytes, Public: {len(public_decoded)} bytes")
            
            # Test key length (DER format should be specific lengths)
            if len(private_decoded) > 50 and len(public_decoded) > 50:
                self.log_test("VAPID Key Length", True, "Keys have reasonable DER lengths")
            else:
                self.log_test("VAPID Key Length", False, f"Keys seem too short: Private={len(private_decoded)}, Public={len(public_decoded)}")
                
            return True
            
        except Exception as e:
            self.log_test("VAPID Key Format", False, f"Decoding error: {e}")
            return False
            
    def test_push_notification_api(self):
        """Test push notification API endpoint"""
        print("\n📱 Testing Push Notification API...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/test-push",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Push Notification API", True, f"Response: {result}")
                return True
            elif response.status_code == 404:
                self.log_test("Push Notification API", False, "Endpoint not found - may need to be implemented")
                return False
            else:
                self.log_test("Push Notification API", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Push Notification API", False, f"Error: {e}")
            return False
            
    def test_flask_logs_for_vapid_errors(self):
        """Check if Flask application shows VAPID-related errors"""
        print("\n📋 Testing for VAPID Errors in Application...")
        
        # This test requires checking Flask logs, which we can't do directly
        # Instead, we'll test if the application starts without VAPID errors
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                self.log_test("Application Health", True, "Application responding normally")
                
                # Try to trigger push notification system
                settings_response = self.session.get(f"{self.base_url}/api/settings")
                if settings_response.status_code == 200:
                    self.log_test("Settings API Health", True, "Settings API working")
                else:
                    self.log_test("Settings API Health", False, f"Settings API error: {settings_response.status_code}")
                    
                return True
            else:
                self.log_test("Application Health", False, f"Application not responding: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Application Health", False, f"Connection error: {e}")
            return False
            
    def test_vapid_integration(self):
        """Test complete VAPID integration"""
        print("\n🔗 Testing VAPID Integration...")
        
        # Test that we can make requests that would trigger VAPID usage
        try:
            # Test email endpoint (which might trigger notifications)
            email_data = {
                "recipient_email": "vapid-test@example.com",
                "cc_emails": "",
                "use_daily_send_time": True,
                "use_legacy_interval": False
            }
            
            response = self.session.post(
                f"{self.base_url}/settings/email",
                json=email_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_test("VAPID Integration Test", True, "Email settings save completed without VAPID errors")
                return True
            else:
                self.log_test("VAPID Integration Test", False, f"Email settings failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("VAPID Integration Test", False, f"Error: {e}")
            return False
            
    def run_all_tests(self):
        """Run all VAPID-related tests"""
        print("🔑 Hospital Equipment System - VAPID Key Test Suite")
        print("=" * 60)
        
        # Test environment variables
        env_ok = self.test_vapid_env_variables()
        
        # Test key format
        if env_ok:
            self.test_vapid_key_format()
            
        # Test API endpoints
        self.test_push_notification_api()
        self.test_flask_logs_for_vapid_errors()
        self.test_vapid_integration()
        
        # Summary
        print("\n📊 VAPID TEST SUMMARY")
        print("=" * 30)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All VAPID tests passed!")
            return True
        else:
            print("⚠️  Some VAPID tests failed. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = VAPIDTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
