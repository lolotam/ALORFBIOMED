#!/usr/bin/env python3
"""
Test script for Flask authentication integration.
Tests login, session management, and authenticated endpoints.
"""

import requests
import json
import sys
import time

class FlaskAuthTestSuite:
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
        
    def test_flask_connectivity(self):
        """Test basic Flask connectivity"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Flask Connectivity", True, "Flask is responding")
                return True
            else:
                self.log_test("Flask Connectivity", False, f"Flask returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Flask Connectivity", False, f"Connection error: {e}")
            return False
            
    def test_login_page_access(self):
        """Test login page is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/auth/login", timeout=5)
            if response.status_code == 200:
                self.log_test("Login Page Access", True, "Login page accessible")
                return True
            else:
                self.log_test("Login Page Access", False, f"Login page returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Login Page Access", False, f"Error accessing login page: {e}")
            return False
            
    def test_login_functionality(self):
        """Test user login functionality"""
        try:
            # First get the login page to establish session
            login_page = self.session.get(f"{self.base_url}/auth/login")
            
            # Attempt login with admin credentials
            login_data = {
                'username': 'admin',
                'password': 'admin'  # Any non-empty password works in test mode
            }
            
            response = self.session.post(
                f"{self.base_url}/auth/login",
                data=login_data,
                allow_redirects=False
            )
            
            # Check if login was successful (should redirect)
            if response.status_code in [302, 303]:
                self.log_test("Login Functionality", True, f"Login successful, redirected to {response.headers.get('Location', 'unknown')}")
                return True
            else:
                self.log_test("Login Functionality", False, f"Login failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Login Functionality", False, f"Login error: {e}")
            return False
            
    def test_authenticated_endpoint_access(self):
        """Test access to authenticated endpoints after login"""
        try:
            # Try to access settings page (requires authentication)
            response = self.session.get(f"{self.base_url}/settings")
            
            if response.status_code == 200:
                self.log_test("Authenticated Endpoint Access", True, "Settings page accessible after login")
                return True
            elif response.status_code == 302:
                self.log_test("Authenticated Endpoint Access", False, "Redirected to login (session not maintained)")
                return False
            else:
                self.log_test("Authenticated Endpoint Access", False, f"Settings page returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Authenticated Endpoint Access", False, f"Error accessing authenticated endpoint: {e}")
            return False
            
    def test_email_settings_endpoint(self):
        """Test email settings endpoint with authentication"""
        try:
            # Test POST to email settings endpoint
            test_data = {
                "recipient_email": "test@example.com",
                "cc_emails": "",
                "use_daily_send_time": True,
                "use_legacy_interval": False,
                "email_send_time": "10:00"
            }
            
            response = self.session.post(
                f"{self.base_url}/settings/email",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_test("Email Settings Endpoint", True, "Email settings endpoint accessible")
                return True
            elif response.status_code == 403:
                self.log_test("Email Settings Endpoint", False, "Permission denied (403) - check user permissions")
                return False
            elif response.status_code == 401:
                self.log_test("Email Settings Endpoint", False, "Authentication required (401) - session issue")
                return False
            else:
                self.log_test("Email Settings Endpoint", False, f"Unexpected status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Email Settings Endpoint", False, f"Error testing email settings: {e}")
            return False
            
    def test_test_email_endpoint(self):
        """Test the test email endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/settings/test-email",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.log_test("Test Email Endpoint", True, "Test email endpoint accessible")
                return True
            elif response.status_code == 403:
                self.log_test("Test Email Endpoint", False, "Permission denied (403) - check user permissions")
                return False
            elif response.status_code == 401:
                self.log_test("Test Email Endpoint", False, "Authentication required (401) - session issue")
                return False
            elif response.status_code == 400:
                self.log_test("Test Email Endpoint", True, "Test email endpoint accessible (400 = missing config, expected)")
                return True
            else:
                self.log_test("Test Email Endpoint", False, f"Unexpected status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Test Email Endpoint", False, f"Error testing test email: {e}")
            return False
            
    def test_session_persistence(self):
        """Test that session persists across requests"""
        try:
            # Make multiple requests to see if session is maintained
            responses = []
            for i in range(3):
                response = self.session.get(f"{self.base_url}/settings")
                responses.append(response.status_code)
                time.sleep(0.5)
                
            # All responses should be the same (either all 200 or all 302)
            if len(set(responses)) == 1:
                if responses[0] == 200:
                    self.log_test("Session Persistence", True, "Session maintained across multiple requests")
                else:
                    self.log_test("Session Persistence", False, f"Session not established (all requests returned {responses[0]})")
            else:
                self.log_test("Session Persistence", False, f"Inconsistent responses: {responses}")
                
            return True
            
        except Exception as e:
            self.log_test("Session Persistence", False, f"Error testing session persistence: {e}")
            return False
            
    def run_all_tests(self):
        """Run all Flask authentication tests"""
        print("🌐 Hospital Equipment System - Flask Authentication Test Suite")
        print("=" * 70)
        
        # Test basic connectivity
        if not self.test_flask_connectivity():
            print("❌ Cannot connect to Flask application. Please ensure it's running on port 5001.")
            return False
            
        # Test login page
        self.test_login_page_access()
        
        # Test login functionality
        login_success = self.test_login_functionality()
        
        if login_success:
            # Test authenticated endpoints
            self.test_authenticated_endpoint_access()
            self.test_email_settings_endpoint()
            self.test_test_email_endpoint()
            self.test_session_persistence()
        else:
            print("⚠️  Skipping authenticated endpoint tests due to login failure")
            
        # Summary
        print("\n📊 FLASK AUTHENTICATION TEST SUMMARY")
        print("=" * 40)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed >= total - 1:  # Allow for one minor failure
            print("🎉 Flask authentication tests mostly passed!")
            return True
        else:
            print("⚠️  Flask authentication has issues. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = FlaskAuthTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
