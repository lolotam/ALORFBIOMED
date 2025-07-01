#!/usr/bin/env python3
"""
Comprehensive test script for Hospital Equipment System settings save functionality.
Tests the specific issues mentioned: Legacy Interval, Daily Send Time, and Automatic Reminders toggles.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:5001"
SETTINGS_FILE_PATH = "app/data/settings.json"

class SettingsTestSuite:
    def __init__(self):
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
        
    def load_current_settings(self):
        """Load current settings from JSON file"""
        try:
            with open(SETTINGS_FILE_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.log_test("Load Settings File", False, f"Error: {e}")
            return None
            
    def test_api_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BASE_URL}/api/health")
            if response.status_code == 200:
                self.log_test("API Connectivity", True, "Health endpoint accessible")
                return True
            else:
                self.log_test("API Connectivity", False, f"Health endpoint returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Connectivity", False, f"Connection error: {e}")
            return False
            
    def test_settings_load_api(self):
        """Test settings loading via API"""
        try:
            response = self.session.get(f"{BASE_URL}/api/settings")
            if response.status_code == 200:
                settings = response.json()
                required_fields = ['use_legacy_interval', 'use_daily_send_time', 'enable_automatic_reminders']
                missing_fields = [field for field in required_fields if field not in settings]
                
                if not missing_fields:
                    self.log_test("Settings Load API", True, f"All required fields present: {required_fields}")
                    return settings
                else:
                    self.log_test("Settings Load API", False, f"Missing fields: {missing_fields}")
                    return None
            else:
                self.log_test("Settings Load API", False, f"API returned {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Settings Load API", False, f"Error: {e}")
            return None
            
    def test_email_settings_save(self):
        """Test email settings save endpoint with scheduling toggles"""
        print("\n🔧 Testing Email Settings Save with Scheduling Toggles...")
        
        # Test data with different combinations
        test_cases = [
            {
                "name": "Daily Send Time Enabled",
                "data": {
                    "recipient_email": "test@example.com",
                    "cc_emails": "cc@example.com",
                    "use_daily_send_time": True,
                    "use_legacy_interval": False,
                    "email_send_time": "10:30"
                }
            },
            {
                "name": "Legacy Interval Enabled", 
                "data": {
                    "recipient_email": "test@example.com",
                    "cc_emails": "cc@example.com",
                    "use_daily_send_time": False,
                    "use_legacy_interval": True,
                    "email_send_time": "09:00"
                }
            }
        ]
        
        for test_case in test_cases:
            try:
                # Save settings
                response = self.session.post(
                    f"{BASE_URL}/settings/email",
                    json=test_case["data"],
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    # Verify settings were saved to file
                    time.sleep(0.5)  # Allow file write to complete
                    saved_settings = self.load_current_settings()
                    
                    if saved_settings:
                        # Check if the specific fields were saved correctly
                        checks = []
                        for key, expected_value in test_case["data"].items():
                            actual_value = saved_settings.get(key)
                            if actual_value == expected_value:
                                checks.append(f"{key}=✅")
                            else:
                                checks.append(f"{key}=❌(expected:{expected_value}, got:{actual_value})")
                        
                        all_correct = all("✅" in check for check in checks)
                        self.log_test(f"Email Settings Save - {test_case['name']}", all_correct, "; ".join(checks))
                    else:
                        self.log_test(f"Email Settings Save - {test_case['name']}", False, "Could not load saved settings")
                else:
                    self.log_test(f"Email Settings Save - {test_case['name']}", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Email Settings Save - {test_case['name']}", False, f"Error: {e}")
                
    def test_reminder_settings_save(self):
        """Test reminder settings save endpoint"""
        print("\n🔧 Testing Reminder Settings Save...")
        
        test_data = {
            "reminder_timing_60_days": True,
            "reminder_timing_14_days": False,
            "reminder_timing_1_day": True,
            "scheduler_interval_hours": 12,
            "enable_automatic_reminders": True
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/settings/reminder",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                time.sleep(0.5)
                saved_settings = self.load_current_settings()
                
                if saved_settings:
                    # Check enable_automatic_reminders specifically
                    actual_value = saved_settings.get('enable_automatic_reminders')
                    expected_value = test_data['enable_automatic_reminders']
                    
                    if actual_value == expected_value:
                        self.log_test("Reminder Settings Save - Automatic Reminders", True, f"enable_automatic_reminders={actual_value}")
                    else:
                        self.log_test("Reminder Settings Save - Automatic Reminders", False, f"Expected {expected_value}, got {actual_value}")
                        
                    # Check scheduler interval
                    actual_interval = saved_settings.get('scheduler_interval_hours')
                    expected_interval = test_data['scheduler_interval_hours']
                    
                    if actual_interval == expected_interval:
                        self.log_test("Reminder Settings Save - Scheduler Interval", True, f"scheduler_interval_hours={actual_interval}")
                    else:
                        self.log_test("Reminder Settings Save - Scheduler Interval", False, f"Expected {expected_interval}, got {actual_interval}")
                else:
                    self.log_test("Reminder Settings Save", False, "Could not load saved settings")
            else:
                self.log_test("Reminder Settings Save", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Reminder Settings Save", False, f"Error: {e}")
            
    def test_settings_persistence(self):
        """Test that settings persist across API calls"""
        print("\n🔧 Testing Settings Persistence...")
        
        # Set specific values
        test_settings = {
            "use_daily_send_time": True,
            "use_legacy_interval": False,
            "enable_automatic_reminders": True
        }
        
        # Save via email endpoint
        email_data = {
            "recipient_email": "persistence@test.com",
            "cc_emails": "",
            **test_settings,
            "email_send_time": "11:45"
        }
        
        try:
            # Save settings
            save_response = self.session.post(
                f"{BASE_URL}/settings/email",
                json=email_data,
                headers={"Content-Type": "application/json"}
            )
            
            if save_response.status_code == 200:
                time.sleep(0.5)
                
                # Load via API
                load_response = self.session.get(f"{BASE_URL}/api/settings")
                
                if load_response.status_code == 200:
                    loaded_settings = load_response.json()
                    
                    persistence_checks = []
                    for key, expected_value in test_settings.items():
                        actual_value = loaded_settings.get(key)
                        if actual_value == expected_value:
                            persistence_checks.append(f"{key}=✅")
                        else:
                            persistence_checks.append(f"{key}=❌(expected:{expected_value}, got:{actual_value})")
                    
                    all_persistent = all("✅" in check for check in persistence_checks)
                    self.log_test("Settings Persistence", all_persistent, "; ".join(persistence_checks))
                else:
                    self.log_test("Settings Persistence", False, f"Failed to load settings: HTTP {load_response.status_code}")
            else:
                self.log_test("Settings Persistence", False, f"Failed to save settings: HTTP {save_response.status_code}")
                
        except Exception as e:
            self.log_test("Settings Persistence", False, f"Error: {e}")
            
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Hospital Equipment System - Settings Save Test Suite")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_api_connectivity():
            print("❌ Cannot connect to Flask application. Please ensure it's running on port 5001.")
            return False
            
        # Test settings loading
        current_settings = self.test_settings_load_api()
        if current_settings:
            print(f"📋 Current settings loaded: {len(current_settings)} fields")
            
        # Test specific functionality
        self.test_email_settings_save()
        self.test_reminder_settings_save()
        self.test_settings_persistence()
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 30)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = SettingsTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
