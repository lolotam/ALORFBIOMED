#!/usr/bin/env python3
"""
Debug test script for Send Message functionality.
Investigates why "Send Message" returns 0 messages sent.
"""

import requests
import json
import sys
import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

class SendMessageDebugTest:
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
            
    def test_settings_configuration(self):
        """Test that settings are properly configured for email notifications"""
        try:
            with open("app/data/settings.json", 'r') as f:
                settings = json.load(f)
                
            # Check critical settings
            email_enabled = settings.get('email_notifications_enabled', False)
            recipient_email = settings.get('recipient_email', '')
            
            checks = []
            if email_enabled:
                checks.append("email_notifications=✅")
            else:
                checks.append("email_notifications=❌")
                
            if recipient_email:
                checks.append(f"recipient=✅({recipient_email})")
            else:
                checks.append("recipient=❌")
                
            all_good = email_enabled and recipient_email
            self.log_test("Settings Configuration", all_good, "; ".join(checks))
            
            return all_good
            
        except Exception as e:
            self.log_test("Settings Configuration", False, f"Error: {e}")
            return False
            
    def test_equipment_data_availability(self):
        """Test that equipment data exists and has future maintenance dates"""
        try:
            # Check PPM data
            with open("app/data/ppm.json", 'r') as f:
                ppm_data = json.load(f)
                
            # Check OCM data
            with open("app/data/ocm.json", 'r') as f:
                ocm_data = json.load(f)
                
            ppm_count = len(ppm_data)
            ocm_count = len(ocm_data)
            
            # Check for future dates in PPM data
            future_ppm_dates = 0
            now = datetime.now()
            
            for entry in ppm_data[:5]:  # Check first 5 entries
                for q_key in ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']:
                    q_data = entry.get(q_key, {})
                    if q_data and q_data.get('quarter_date'):
                        try:
                            # Parse date in DD/MM/YYYY format
                            date_str = q_data['quarter_date']
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            if date_obj > now:
                                future_ppm_dates += 1
                        except:
                            pass
                            
            # Check for future dates in OCM data
            future_ocm_dates = 0
            for entry in ocm_data[:5]:  # Check first 5 entries
                next_maintenance = entry.get('Next_Maintenance')
                if next_maintenance and next_maintenance != 'N/A':
                    try:
                        date_obj = datetime.strptime(next_maintenance, '%d/%m/%Y')
                        if date_obj > now:
                            future_ocm_dates += 1
                    except:
                        pass
                        
            details = f"PPM: {ppm_count} entries ({future_ppm_dates} future dates), OCM: {ocm_count} entries ({future_ocm_dates} future dates)"
            has_data = ppm_count > 0 and ocm_count > 0 and (future_ppm_dates > 0 or future_ocm_dates > 0)
            
            self.log_test("Equipment Data Availability", has_data, details)
            return has_data
            
        except Exception as e:
            self.log_test("Equipment Data Availability", False, f"Error: {e}")
            return False
            
    def test_email_service_process_reminders_direct(self):
        """Test the EmailService.process_reminders method directly"""
        try:
            from app.services.email_service import EmailService
            
            # Run the async method directly
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                print("   Running EmailService.process_reminders() directly...")
                emails_sent = loop.run_until_complete(EmailService.process_reminders())
                
                if emails_sent is None:
                    self.log_test("Direct Process Reminders", False, "Method returned None (likely disabled or error)")
                elif emails_sent == 0:
                    self.log_test("Direct Process Reminders", False, "Method returned 0 emails sent")
                else:
                    self.log_test("Direct Process Reminders", True, f"Method returned {emails_sent} emails sent")
                    
                return emails_sent
                
            finally:
                loop.close()
                
        except Exception as e:
            self.log_test("Direct Process Reminders", False, f"Error: {e}")
            return None
            
    def test_upcoming_maintenance_detection(self):
        """Test if the system can detect upcoming maintenance"""
        try:
            from app.services.email_service import EmailService
            from app.services.data_service import DataService
            
            # Load data
            ppm_data = DataService.load_data('ppm')
            ocm_data = DataService.load_data('ocm')
            
            # Test different thresholds
            thresholds = [
                (0, 1, 'URGENT'),
                (2, 7, 'HIGH'),
                (8, 15, 'MEDIUM'),
                (16, 30, 'LOW'),
                (0, 365, 'ALL')  # Check everything in the next year
            ]
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                total_found = 0
                details = []
                
                for min_days, max_days, priority in thresholds:
                    upcoming_ppm = loop.run_until_complete(
                        EmailService.get_upcoming_maintenance_by_days(ppm_data, 'ppm', min_days, max_days)
                    )
                    upcoming_ocm = loop.run_until_complete(
                        EmailService.get_upcoming_maintenance_by_days(ocm_data, 'ocm', min_days, max_days)
                    )
                    
                    ppm_count = len(upcoming_ppm)
                    ocm_count = len(upcoming_ocm)
                    threshold_total = ppm_count + ocm_count
                    total_found += threshold_total
                    
                    if threshold_total > 0:
                        details.append(f"{priority}: {threshold_total} ({ppm_count} PPM, {ocm_count} OCM)")
                        
                if total_found > 0:
                    self.log_test("Upcoming Maintenance Detection", True, f"Found {total_found} upcoming tasks: {'; '.join(details)}")
                else:
                    self.log_test("Upcoming Maintenance Detection", False, "No upcoming maintenance found in any threshold")
                    
                return total_found
                
            finally:
                loop.close()
                
        except Exception as e:
            self.log_test("Upcoming Maintenance Detection", False, f"Error: {e}")
            return 0
            
    def test_send_message_api_endpoint(self):
        """Test the actual Send Message API endpoint"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/send-immediate-reminders",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                emails_sent = result.get('emails_sent', 0)
                message = result.get('message', '')
                
                if emails_sent > 0:
                    self.log_test("Send Message API Endpoint", True, f"API returned {emails_sent} emails sent: {message}")
                else:
                    self.log_test("Send Message API Endpoint", False, f"API returned 0 emails sent: {message}")
                    
                return emails_sent
                
            else:
                result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error = result.get('error', response.text)
                self.log_test("Send Message API Endpoint", False, f"API returned {response.status_code}: {error}")
                return 0
                
        except Exception as e:
            self.log_test("Send Message API Endpoint", False, f"Error: {e}")
            return 0
            
    def run_debug_tests(self):
        """Run all debug tests for Send Message functionality"""
        print("🔍 Hospital Equipment System - Send Message Debug Test")
        print("=" * 65)
        print("Investigating why Send Message returns 0 messages sent...")
        print()
        
        # Login first
        if not self.login_as_admin():
            print("❌ Cannot proceed without admin login")
            return False
            
        # Test configuration
        print("\n🔧 Testing Configuration...")
        self.test_settings_configuration()
        
        # Test data availability
        print("\n📊 Testing Data Availability...")
        self.test_equipment_data_availability()
        
        # Test upcoming maintenance detection
        print("\n🔍 Testing Maintenance Detection...")
        upcoming_count = self.test_upcoming_maintenance_detection()
        
        # Test direct method call
        print("\n⚙️ Testing Direct Method Call...")
        direct_result = self.test_email_service_process_reminders_direct()
        
        # Test API endpoint
        print("\n🌐 Testing API Endpoint...")
        api_result = self.test_send_message_api_endpoint()
        
        # Summary
        print("\n📊 DEBUG TEST SUMMARY")
        print("=" * 40)
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        print(f"Passed: {passed}/{total}")
        
        print(f"\n🔍 KEY FINDINGS:")
        print(f"   - Upcoming maintenance tasks found: {upcoming_count}")
        print(f"   - Direct method result: {direct_result}")
        print(f"   - API endpoint result: {api_result}")
        
        if upcoming_count > 0 and (direct_result == 0 or api_result == 0):
            print("\n⚠️  ISSUE IDENTIFIED:")
            print("   Equipment data exists with upcoming maintenance,")
            print("   but Send Message functionality returns 0 emails sent.")
            print("   This suggests a logic issue in the reminder processing.")
        elif upcoming_count == 0:
            print("\n⚠️  ISSUE IDENTIFIED:")
            print("   No upcoming maintenance found in any threshold.")
            print("   This could be due to date parsing or filtering issues.")
        else:
            print("\n✅ Send Message functionality appears to be working correctly.")
            
        return passed >= total - 2  # Allow for minor failures

if __name__ == "__main__":
    tester = SendMessageDebugTest()
    success = tester.run_debug_tests()
    sys.exit(0 if success else 1)
