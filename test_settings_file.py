#!/usr/bin/env python3
"""
Test script to verify settings file structure and our fixes.
This tests the file-level functionality without requiring Flask to be running.
"""

import json
import sys
from pathlib import Path

class SettingsFileTestSuite:
    def __init__(self):
        self.settings_file = Path("app/data/settings.json")
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
        
    def test_settings_file_exists(self):
        """Test that settings file exists"""
        if self.settings_file.exists():
            self.log_test("Settings File Exists", True, f"Found at {self.settings_file}")
            return True
        else:
            self.log_test("Settings File Exists", False, f"Not found at {self.settings_file}")
            return False
            
    def test_settings_file_structure(self):
        """Test that settings file has correct structure"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                
            # Check for required fields that were causing issues
            required_fields = [
                'use_legacy_interval',
                'use_daily_send_time', 
                'enable_automatic_reminders',
                'email_send_time'
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in settings:
                    present_fields.append(f"{field}={settings[field]}")
                else:
                    missing_fields.append(field)
                    
            if not missing_fields:
                self.log_test("Settings File Structure", True, f"All required fields present: {'; '.join(present_fields)}")
                return settings
            else:
                self.log_test("Settings File Structure", False, f"Missing fields: {missing_fields}")
                return None
                
        except json.JSONDecodeError as e:
            self.log_test("Settings File Structure", False, f"JSON decode error: {e}")
            return None
        except Exception as e:
            self.log_test("Settings File Structure", False, f"Error reading file: {e}")
            return None
            
    def test_settings_logic_consistency(self):
        """Test that settings have logical consistency"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                
            # Test 1: Legacy interval and daily send time should be mutually exclusive
            use_legacy = settings.get('use_legacy_interval', False)
            use_daily = settings.get('use_daily_send_time', True)
            
            if use_legacy and use_daily:
                self.log_test("Settings Logic - Mutual Exclusivity", False, "Both legacy interval and daily send time are enabled")
            elif not use_legacy and not use_daily:
                self.log_test("Settings Logic - Mutual Exclusivity", False, "Neither legacy interval nor daily send time are enabled")
            else:
                self.log_test("Settings Logic - Mutual Exclusivity", True, f"Correctly configured: legacy={use_legacy}, daily={use_daily}")
                
            # Test 2: If daily send time is enabled, email_send_time should be set
            if use_daily:
                email_time = settings.get('email_send_time')
                if email_time:
                    self.log_test("Settings Logic - Email Time", True, f"Daily send time enabled with time: {email_time}")
                else:
                    self.log_test("Settings Logic - Email Time", False, "Daily send time enabled but no email_send_time set")
            else:
                self.log_test("Settings Logic - Email Time", True, "Legacy interval mode, email_send_time not required")
                
            # Test 3: Automatic reminders setting
            auto_reminders = settings.get('enable_automatic_reminders', False)
            self.log_test("Settings Logic - Auto Reminders", True, f"Automatic reminders: {auto_reminders}")
            
            return True
            
        except Exception as e:
            self.log_test("Settings Logic Consistency", False, f"Error: {e}")
            return False
            
    def test_settings_modification(self):
        """Test modifying settings and saving them back"""
        try:
            # Load current settings
            with open(self.settings_file, 'r') as f:
                original_settings = json.load(f)
                
            # Create test settings
            test_settings = original_settings.copy()
            test_settings.update({
                'use_legacy_interval': False,
                'use_daily_send_time': True,
                'enable_automatic_reminders': True,
                'email_send_time': '14:30',
                'test_marker': 'settings_test_suite'
            })
            
            # Save test settings
            with open(self.settings_file, 'w') as f:
                json.dump(test_settings, f, indent=2)
                
            # Verify they were saved
            with open(self.settings_file, 'r') as f:
                saved_settings = json.load(f)
                
            # Check if our test values were saved correctly
            checks = []
            test_values = {
                'use_legacy_interval': False,
                'use_daily_send_time': True,
                'enable_automatic_reminders': True,
                'email_send_time': '14:30',
                'test_marker': 'settings_test_suite'
            }
            
            for key, expected_value in test_values.items():
                actual_value = saved_settings.get(key)
                if actual_value == expected_value:
                    checks.append(f"{key}=✅")
                else:
                    checks.append(f"{key}=❌(expected:{expected_value}, got:{actual_value})")
                    
            # Restore original settings
            with open(self.settings_file, 'w') as f:
                json.dump(original_settings, f, indent=2)
                
            all_correct = all("✅" in check for check in checks)
            self.log_test("Settings File Modification", all_correct, "; ".join(checks))
            
            return all_correct
            
        except Exception as e:
            self.log_test("Settings File Modification", False, f"Error: {e}")
            return False
            
    def test_template_fix_verification(self):
        """Verify that our template fixes are correct"""
        print("\n🔧 Verifying Template Fixes...")
        
        # Check the settings.html template for the fix we made
        template_file = Path("app/templates/settings.html")
        
        if not template_file.exists():
            self.log_test("Template File Exists", False, "settings.html not found")
            return False
            
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
                
            # Check for the corrected logic
            if 'settings.use_legacy_interval %}checked{% endif %}' in template_content:
                self.log_test("Template Fix - Legacy Interval", True, "Correct logic: {% if settings.use_legacy_interval %}")
            elif 'not settings.use_daily_send_time %}checked{% endif %}' in template_content:
                self.log_test("Template Fix - Legacy Interval", False, "Old incorrect logic still present")
            else:
                self.log_test("Template Fix - Legacy Interval", False, "Could not find legacy interval toggle logic")
                
            # Check for daily send time toggle
            if 'settings.use_daily_send_time %}checked{% endif %}' in template_content:
                self.log_test("Template Fix - Daily Send Time", True, "Correct logic: {% if settings.use_daily_send_time %}")
            else:
                self.log_test("Template Fix - Daily Send Time", False, "Daily send time toggle logic not found")
                
            # Check for automatic reminders toggle
            if 'settings.enable_automatic_reminders %}checked{% endif %}' in template_content:
                self.log_test("Template Fix - Auto Reminders", True, "Correct logic: {% if settings.enable_automatic_reminders %}")
            else:
                self.log_test("Template Fix - Auto Reminders", False, "Auto reminders toggle logic not found")
                
            return True
            
        except Exception as e:
            self.log_test("Template Fix Verification", False, f"Error reading template: {e}")
            return False
            
    def run_all_tests(self):
        """Run all file-level tests"""
        print("📁 Hospital Equipment System - Settings File Test Suite")
        print("=" * 60)
        
        # Test file existence
        if not self.test_settings_file_exists():
            print("❌ Cannot proceed without settings file")
            return False
            
        # Test file structure
        settings = self.test_settings_file_structure()
        if settings:
            print(f"📋 Current settings: {len(settings)} fields loaded")
            
        # Test logic consistency
        self.test_settings_logic_consistency()
        
        # Test file modification
        self.test_settings_modification()
        
        # Test template fixes
        self.test_template_fix_verification()
        
        # Summary
        print("\n📊 FILE TEST SUMMARY")
        print("=" * 30)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed == total:
            print("🎉 All file-level tests passed!")
            return True
        else:
            print("⚠️  Some file-level tests failed. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = SettingsFileTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
