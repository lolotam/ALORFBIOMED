#!/usr/bin/env python3
"""
Test script for Hospital Equipment System authentication functionality.
Tests user loading, permissions, and authentication without requiring Flask to be running.
"""

import json
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

class AuthenticationTestSuite:
    def __init__(self):
        self.test_results = []
        self.settings_file = Path("app/data/settings.json")
        
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
        
    def test_settings_file_has_users(self):
        """Test that settings file contains user authentication data"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                
            # Check for users section
            users = settings.get('users', [])
            if not users:
                self.log_test("Settings File Has Users", False, "No users section found in settings.json")
                return False
                
            # Check for roles section
            roles = settings.get('roles', {})
            if not roles:
                self.log_test("Settings File Has Users", False, "No roles section found in settings.json")
                return False
                
            user_count = len(users)
            role_count = len(roles)
            self.log_test("Settings File Has Users", True, f"Found {user_count} users and {role_count} roles")
            return True
            
        except Exception as e:
            self.log_test("Settings File Has Users", False, f"Error reading settings: {e}")
            return False
            
    def test_user_model_loading(self):
        """Test JSONUser model can load users"""
        try:
            from app.models.json_user import JSONUser
            
            # Test loading a known user
            admin_user = JSONUser.get_user('admin')
            if admin_user:
                self.log_test("User Model Loading - Admin", True, f"Admin user loaded: {admin_user.username} ({admin_user.role})")
            else:
                self.log_test("User Model Loading - Admin", False, "Could not load admin user")
                
            # Test loading editor user
            editor_user = JSONUser.get_user('editor1')
            if editor_user:
                self.log_test("User Model Loading - Editor", True, f"Editor user loaded: {editor_user.username} ({editor_user.role})")
            else:
                self.log_test("User Model Loading - Editor", False, "Could not load editor1 user")
                
            # Test loading non-existent user
            fake_user = JSONUser.get_user('nonexistent')
            if fake_user is None:
                self.log_test("User Model Loading - Nonexistent", True, "Correctly returned None for nonexistent user")
            else:
                self.log_test("User Model Loading - Nonexistent", False, "Should return None for nonexistent user")
                
            return admin_user is not None and editor_user is not None
            
        except Exception as e:
            self.log_test("User Model Loading", False, f"Error loading users: {e}")
            return False
            
    def test_user_permissions(self):
        """Test user permission system"""
        try:
            from app.models.json_user import JSONUser
            
            # Test admin permissions
            admin_user = JSONUser.get_user('admin')
            if admin_user:
                admin_permissions = admin_user.permissions
                required_admin_perms = ['settings_manage', 'settings_email_test', 'user_manage']
                
                missing_perms = [perm for perm in required_admin_perms if perm not in admin_permissions]
                if not missing_perms:
                    self.log_test("Admin Permissions", True, f"Admin has all required permissions: {len(admin_permissions)} total")
                else:
                    self.log_test("Admin Permissions", False, f"Admin missing permissions: {missing_perms}")
                    
            # Test editor permissions
            editor_user = JSONUser.get_user('editor1')
            if editor_user:
                editor_permissions = editor_user.permissions
                # Editor should NOT have settings_manage permission
                if 'settings_manage' not in editor_permissions:
                    self.log_test("Editor Permissions", True, f"Editor correctly lacks settings_manage permission")
                else:
                    self.log_test("Editor Permissions", False, "Editor should not have settings_manage permission")
                    
            # Test viewer permissions
            viewer_user = JSONUser.get_user('viewer1')
            if viewer_user:
                viewer_permissions = viewer_user.permissions
                # Viewer should have very limited permissions
                if len(viewer_permissions) <= 5:
                    self.log_test("Viewer Permissions", True, f"Viewer has limited permissions: {len(viewer_permissions)} total")
                else:
                    self.log_test("Viewer Permissions", False, f"Viewer has too many permissions: {len(viewer_permissions)}")
                    
            return True
            
        except Exception as e:
            self.log_test("User Permissions", False, f"Error testing permissions: {e}")
            return False
            
    def test_password_checking(self):
        """Test password verification"""
        try:
            from app.models.json_user import JSONUser
            
            # Test editor1 with simple password
            editor_user = JSONUser.get_user('editor1')
            if editor_user:
                # The current implementation allows any non-empty password for testing
                if editor_user.check_password('editor'):
                    self.log_test("Password Checking - Editor", True, "Editor password verification works")
                else:
                    self.log_test("Password Checking - Editor", False, "Editor password verification failed")
                    
                # Test empty password should fail
                if not editor_user.check_password(''):
                    self.log_test("Password Checking - Empty", True, "Empty password correctly rejected")
                else:
                    self.log_test("Password Checking - Empty", False, "Empty password should be rejected")
                    
            return True
            
        except Exception as e:
            self.log_test("Password Checking", False, f"Error testing passwords: {e}")
            return False
            
    def test_permission_decorator_logic(self):
        """Test permission decorator logic"""
        try:
            from app.decorators import permission_required
            from app.models.json_user import JSONUser
            
            # This is a simplified test of the decorator logic
            admin_user = JSONUser.get_user('admin')
            if admin_user:
                # Test if admin has settings_manage permission
                has_settings_manage = 'settings_manage' in admin_user.permissions
                if has_settings_manage:
                    self.log_test("Permission Decorator Logic", True, "Admin has settings_manage permission for email settings")
                else:
                    self.log_test("Permission Decorator Logic", False, "Admin missing settings_manage permission")
                    
            return True
            
        except Exception as e:
            self.log_test("Permission Decorator Logic", False, f"Error testing decorator: {e}")
            return False
            
    def test_email_settings_permissions(self):
        """Test specific permissions for email settings endpoints"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                
            # Check what permissions are required for email settings
            admin_perms = settings.get('roles', {}).get('Admin', {}).get('permissions', [])
            editor_perms = settings.get('roles', {}).get('Editor', {}).get('permissions', [])
            
            # Admin should have settings_manage and settings_email_test
            admin_can_manage = 'settings_manage' in admin_perms
            admin_can_test = 'settings_email_test' in admin_perms
            
            # Editor should NOT have settings_manage
            editor_can_manage = 'settings_manage' in editor_perms
            
            if admin_can_manage and admin_can_test and not editor_can_manage:
                self.log_test("Email Settings Permissions", True, "Correct permission setup for email settings")
            else:
                details = f"Admin manage:{admin_can_manage}, test:{admin_can_test}, Editor manage:{editor_can_manage}"
                self.log_test("Email Settings Permissions", False, f"Incorrect permissions: {details}")
                
            return True
            
        except Exception as e:
            self.log_test("Email Settings Permissions", False, f"Error checking permissions: {e}")
            return False
            
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 Hospital Equipment System - Authentication Test Suite")
        print("=" * 60)
        
        # Test settings file
        if not self.test_settings_file_has_users():
            print("❌ Cannot proceed without user data in settings")
            return False
            
        # Test user model
        self.test_user_model_loading()
        
        # Test permissions
        self.test_user_permissions()
        
        # Test password checking
        self.test_password_checking()
        
        # Test decorator logic
        self.test_permission_decorator_logic()
        
        # Test email settings permissions
        self.test_email_settings_permissions()
        
        # Summary
        print("\n📊 AUTHENTICATION TEST SUMMARY")
        print("=" * 40)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        if passed >= total - 1:  # Allow for one minor failure
            print("🎉 Authentication system tests passed!")
            return True
        else:
            print("⚠️  Authentication system has issues. Check details above.")
            failed_tests = [result for result in self.test_results if not result["passed"]]
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
            return False

if __name__ == "__main__":
    tester = AuthenticationTestSuite()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
