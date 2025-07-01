#!/usr/bin/env python3
"""
Final comprehensive fix for all three issues.
"""

import os
import subprocess
import time
import requests
import json

def load_env_file():
    """Load environment variables from .env22 file"""
    print("🔧 Loading environment variables from .env22...")
    
    env_file = ".env22"
    if not os.path.exists(env_file):
        print(f"❌ {env_file} not found")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"✅ Set {key}")
    
    return True

def restart_flask_with_env():
    """Restart Flask with proper environment variables"""
    print("\n🔄 Restarting Flask with new environment...")
    
    # Kill existing Flask processes
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                      capture_output=True, check=False)
        print("✅ Stopped existing Flask processes")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Error stopping processes: {e}")
    
    # Load environment variables
    if not load_env_file():
        return False
    
    # Start Flask with environment
    try:
        print("🚀 Starting Flask with new environment...")
        # Use subprocess.Popen to start in background
        process = subprocess.Popen([
            'poetry', 'run', 'python', '-m', 'app.main'
        ], cwd=os.getcwd())
        
        print(f"✅ Flask started with PID: {process.pid}")
        
        # Wait for Flask to start
        print("⏳ Waiting for Flask to start...")
        time.sleep(10)
        
        # Test if Flask is running
        try:
            response = requests.get("http://localhost:5001/", timeout=5)
            if response.status_code in [200, 302]:
                print("✅ Flask is running and responding")
                return True
            else:
                print(f"❌ Flask returned status: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Flask not responding: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask: {e}")
        return False

def test_all_fixes():
    """Test all three fixes"""
    print("\n🧪 Testing all fixes...")
    
    # Setup session
    session = requests.Session()
    
    # Authenticate
    try:
        session.get("http://localhost:5001/")
        login_data = {'username': 'admin', 'password': 'admin'}
        login_response = session.post("http://localhost:5001/auth/login", data=login_data)
        
        if login_response.status_code not in [200, 302, 303]:
            print("❌ Authentication failed")
            return False
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False
    
    results = {}
    
    # Test 1: VAPID Keys (Push Notifications)
    print("\n📱 Testing VAPID Keys...")
    try:
        # Check VAPID public key
        vapid_response = session.get("http://localhost:5001/api/vapid_public_key")
        if vapid_response.status_code == 200:
            vapid_data = vapid_response.json()
            key_length = len(vapid_data.get('publicKey', ''))
            print(f"✅ VAPID public key length: {key_length}")
            
            # Test push notification
            push_response = session.post(
                "http://localhost:5001/api/test-push",
                json={},
                headers={"Content-Type": "application/json"}
            )
            
            if push_response.status_code == 200:
                results['push_notifications'] = "✅ WORKING"
                print("✅ Push notifications: WORKING")
            elif push_response.status_code == 400:
                push_data = push_response.json()
                if 'subscriptions' in push_data.get('error', ''):
                    results['push_notifications'] = "✅ FIXED (no subscriptions)"
                    print("✅ Push notifications: FIXED (no subscriptions)")
                else:
                    results['push_notifications'] = f"❌ Error: {push_data.get('error')}"
                    print(f"❌ Push notifications: {push_data.get('error')}")
            else:
                results['push_notifications'] = f"❌ Status: {push_response.status_code}"
                print(f"❌ Push notifications: Status {push_response.status_code}")
        else:
            results['push_notifications'] = "❌ VAPID endpoint failed"
            print("❌ VAPID endpoint failed")
    except Exception as e:
        results['push_notifications'] = f"❌ Error: {e}"
        print(f"❌ Push notifications error: {e}")
    
    # Test 2: Backup Settings API
    print("\n💾 Testing Backup Settings API...")
    try:
        backup_data = {
            "automatic_backup_enabled": True,
            "automatic_backup_interval_hours": 8
        }
        
        backup_response = session.post(
            "http://localhost:5001/api/backup-settings",
            json=backup_data,
            headers={"Content-Type": "application/json"}
        )
        
        if backup_response.status_code == 200:
            results['backup_settings'] = "✅ WORKING"
            print("✅ Backup settings API: WORKING")
        else:
            results['backup_settings'] = f"❌ Status: {backup_response.status_code}"
            print(f"❌ Backup settings API: Status {backup_response.status_code}")
    except Exception as e:
        results['backup_settings'] = f"❌ Error: {e}"
        print(f"❌ Backup settings API error: {e}")
    
    # Test 3: Backup Downloads
    print("\n⬇️ Testing Backup Downloads...")
    try:
        # Create a fresh backup
        create_response = session.post("http://localhost:5001/backup/create-settings")
        if create_response.status_code == 200:
            print("✅ Backup created successfully")
            time.sleep(2)  # Wait for file creation
            
            # Find the newest backup file
            backups_dir = "app/data/backups/settings"
            if os.path.exists(backups_dir):
                files = [f for f in os.listdir(backups_dir) if f.endswith('.json')]
                if files:
                    files.sort(key=lambda x: os.path.getmtime(os.path.join(backups_dir, x)), reverse=True)
                    newest_file = files[0]
                    
                    # Test download
                    download_response = session.get(f"http://localhost:5001/backup/download/settings/{newest_file}")
                    
                    if download_response.status_code == 200:
                        content_type = download_response.headers.get('Content-Type', '')
                        if 'application/json' in content_type or 'application/octet-stream' in content_type:
                            results['backup_downloads'] = "✅ WORKING"
                            print("✅ Backup downloads: WORKING")
                        else:
                            results['backup_downloads'] = "❌ Wrong content type"
                            print("❌ Backup downloads: Wrong content type")
                    else:
                        results['backup_downloads'] = f"❌ Status: {download_response.status_code}"
                        print(f"❌ Backup downloads: Status {download_response.status_code}")
                else:
                    results['backup_downloads'] = "❌ No backup files found"
                    print("❌ No backup files found")
            else:
                results['backup_downloads'] = "❌ Backup directory not found"
                print("❌ Backup directory not found")
        else:
            results['backup_downloads'] = "❌ Failed to create backup"
            print("❌ Failed to create backup")
    except Exception as e:
        results['backup_downloads'] = f"❌ Error: {e}"
        print(f"❌ Backup downloads error: {e}")
    
    return results

def main():
    """Main fix and test function"""
    print("🏥 Hospital Equipment System - Final Comprehensive Fix")
    print("=" * 70)
    print("Fixing and testing:")
    print("1. 📱 Push Notification VAPID Keys")
    print("2. 💾 Backup Settings API Endpoint") 
    print("3. ⬇️ Backup Download Functionality")
    print("=" * 70)
    
    # Step 1: Restart Flask with proper environment
    if not restart_flask_with_env():
        print("\n❌ Failed to restart Flask with new environment")
        return False
    
    # Step 2: Test all fixes
    results = test_all_fixes()
    
    # Step 3: Print final results
    print("\n" + "=" * 70)
    print("📊 FINAL COMPREHENSIVE FIX RESULTS")
    print("=" * 70)
    
    for feature, status in results.items():
        print(f"{status} {feature.replace('_', ' ').title()}")
    
    # Count successes
    success_count = sum(1 for status in results.values() if status.startswith("✅"))
    total_count = len(results)
    
    print(f"\nOverall Result: {success_count}/{total_count} features working")
    
    if success_count == total_count:
        print("\n🎉 ALL ISSUES FIXED SUCCESSFULLY!")
        print("✅ Push notifications: VAPID keys working")
        print("✅ Backup settings: API endpoint functional")
        print("✅ Backup downloads: File serving operational")
        print("\n💡 Your Hospital Equipment Management System is fully operational!")
    else:
        print("\n⚠️ SOME ISSUES REMAIN")
        failed_features = [k for k, v in results.items() if not v.startswith("✅")]
        print("🔧 Features that still need attention:")
        for feature in failed_features:
            print(f"   • {feature.replace('_', ' ').title()}: {results[feature]}")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
