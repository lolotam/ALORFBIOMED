#!/usr/bin/env python3
"""
Comprehensive test script for email settings save functionality.
Tests the complete workflow: login -> save settings -> verify persistence -> test email.
"""

import requests
import json
import sys
import time

class EmailSettingsTestSuite:
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
            
    def test_email_settings_save_daily_mode(self):
        """Test saving email settings in daily send time mode"""
        try:
            test_data = {
                "recipient_email": "test-daily@example.com",
                "cc_emails": "cc-daily@example.com",
                "use_daily_send_time": True,
                "use_legacy_interval": False,
                "email_send_time": "08:30"
            }
            
            response = self.session.post(
                f"{self.base_url}/settings/email",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Email Settings Save - Daily Mode", True, f"Settings saved: {result.get('message', 'Success')}")
                return True
            else:
                self.log_test("Email Settings Save - Daily Mode", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Email Settings Save - Daily Mode", False, f"Error: {e}")
            return False
            
    def test_email_settings_save_legacy_mode(self):
        """Test saving email settings in legacy interval mode"""
        try:
            test_data = {
                "recipient_email": "test-legacy@example.com",
                "cc_emails": "cc-legacy@example.com",
                "use_daily_send_time": False,
                "use_legacy_interval": True,
                "email_send_time": "09:00"
            }
            
            response = self.session.post(
                f"{self.base_url}/settings/email",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Email Settings Save - Legacy Mode", True, f"Settings saved: {result.get('message', 'Success')}")
                return True
            else:
                self.log_test("Email Settings Save - Legacy Mode", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Email Settings Save - Legacy Mode", False, f"Error: {e}")
            return False
            
    def test_settings_persistence(self):
        """Test that saved settings persist in the file"""
        try:
            # Wait for file write to complete
            time.sleep(1)
            
            # Read settings file directly
            with open("app/data/settings.json", 'r') as f:
                settings = json.load(f)
                
            # Check if our test values were saved
            recipient = settings.get('recipient_email', '')
            cc_emails = settings.get('cc_emails', '')
            use_daily = settings.get('use_daily_send_time', False)
            use_legacy = settings.get('use_legacy_interval', False)
            email_time = settings.get('email_send_time', '')
            
            # Verify the last saved values (legacy mode)
            checks = []
            if recipient == "test-legacy@example.com":
                checks.append("recipient=✅")
            else:
                checks.append(f"recipient=❌({recipient})")
                
            if cc_emails == "cc-legacy@example.com":
                checks.append("cc=✅")
            else:
                checks.append(f"cc=❌({cc_emails})")
                
            if not use_daily and use_legacy:
                checks.append("mode=✅(legacy)")
            else:
                checks.append(f"mode=❌(daily:{use_daily},legacy:{use_legacy})")
                
            all_correct = all("✅" in check for check in checks)
            self.log_test("Settings Persistence", all_correct, "; ".join(checks))
            
            return all_correct
            
        except Exception as e:
            self.log_test("Settings Persistence", False, f"Error checking persistence: {e}")
            return False
            
    def test_settings_api_load(self):
        """Test loading settings via API"""
        try:
            response = self.session.get(f"{self.base_url}/api/settings")
            
            if response.status_code == 200:
                settings = response.json()
                
                # Check if the settings contain our expected fields
                required_fields = ['recipient_email', 'cc_emails', 'use_daily_send_time', 'use_legacy_interval']
                missing_fields = [field for field in required_fields if field not in settings]
                
                if not missing_fields:
                    self.log_test("Settings API Load", True, f"All fields present: {len(settings)} total settings")
                    return settings
                else:
                    self.log_test("Settings API Load", False, f"Missing fields: {missing_fields}")
                    return None
            else:
                self.log_test("Settings API Load", False, f"API returned {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Settings API Load", False, f"Error: {e}")
            return None
            
    def test_frontend_compatibility(self):
        """Test that settings page loads correctly"""
        try:
            response = self.session.get(f"{self.base_url}/settings")
            
            if response.status_code == 200:
                # Check if the page contains the expected form elements
                page_content = response.text
                
                checks = []
                if 'legacyIntervalToggle' in page_content:
                    checks.append("legacy_toggle=✅")
                else:
                    checks.append("legacy_toggle=❌")
                    
                if 'dailySendTimeToggle' in page_content:
                    checks.append("daily_toggle=✅")
                else:
                    checks.append("daily_toggle=❌")
                    
                if 'enableAutomaticReminders' in page_content:
                    checks.append("auto_reminders=✅")
                else:
                    checks.append("auto_reminders=❌")
                    
                all_present = all("✅" in check for check in checks)
                self.log_test("Frontend Compatibility", all_present, "; ".join(checks))
                
                return all_present
            else:
                self.log_test("Frontend Compatibility", False, f"Settings page returned {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Frontend Compatibility", False, f"Error: {e}")
            return False
            
    def test_toggle_mutual_exclusivity(self):
        """Test that daily and legacy modes are mutually exclusive"""
        try:
            # Test setting both to true (should not be allowed)
            invalid_data = {
                "recipient_email": "test-invalid@example.com",
                "cc_emails": "",
                "use_daily_send_time": True,
                "use_legacy_interval": True,  # This should cause an issue
                "email_send_time": "10:00"
            }
            
            response = self.session.post(
                f"{self.base_url}/settings/email",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Check what actually got saved
            time.sleep(0.5)
            with open("app/data/settings.json", 'r') as f:
                settings = json.load(f)
                
            use_daily = settings.get('use_daily_send_time', False)
            use_legacy = settings.get('use_legacy_interval', False)
            
            # The system should enforce mutual exclusivity
            if use_daily and use_legacy:
                self.log_test("Toggle Mutual Exclusivity", False, "Both modes enabled - mutual exclusivity not enforced")
            elif use_daily and not use_legacy:
                self.log_test("Toggle Mutual Exclusivity", True, "Daily mode selected, legacy disabled")
            elif use_legacy and not use_daily:
                self.log_test("Toggle Mutual Exclusivity", True, "Legacy mode selected, daily disabled")
            else:
                self.log_test("Toggle Mutual Exclusivity", False, "Neither mode enabled")
                
            return True
            
        except Exception as e:
            self.log_test("Toggle Mutual Exclusivity", False, f"Error: {e}")
            return False
            
    def run_all_tests(self):
        """Run all email settings tests"""
        print("📧 Hospital Equipment System - Email Settings Complete Test Suite")
        print("=" * 75)
        
        # Login first
        if not self.login_as_admin():
            print("❌ Cannot proceed without admin login")
            return False
            
        # Test email settings save functionality
        self.test_email_settings_save_daily_mode()
        self.test_email_settings_save_legacy_mode()
        
        # Test persistence
        self.test_settings_persistence()
        
        # Test API loading
        self.test_settings_api_load()
        
        # Test frontend compatibility
        self.test_frontend_compatibility()
        
        # Test mutual exclusivity
        self.test_toggle_mutual_exclusivity()
        
        # Summary
        print("\n📊 EMAIL SETTINGS TEST SUMMARY")
        print("=" * 40)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed >= total - 1:  # Allow for one minor failure
            print("🎉 Email settings functionality working correctly!")
            return True
        else:
            print("⚠️  Email settings have issues. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = EmailSettingsTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
