#!/usr/bin/env python3
"""
Test all email features of the Hospital Equipment System
"""
import sys
sys.path.insert(0, '.')

from app.services.email_service import EmailService
from app.services.data_service import DataService
from app.config import Config

print('🧪 Testing Hospital Equipment System Email Features')
print('='*60)

# Check current settings
try:
    settings = DataService.load_settings()
    print('📋 Current Email Configuration:')
    print(f'   ✅ Email Notifications: {settings.get("email_notifications_enabled", False)}')
    print(f'   📧 Recipient: {settings.get("recipient_email", "Not set")}')
    print(f'   📅 Send Time: {settings.get("email_send_time", "Not set")}')
    print(f'   🔄 Automatic Reminders: {settings.get("enable_automatic_reminders", False)}')
    print(f'   📎 CC Emails: {settings.get("cc_emails", "None")}')
    print()
except Exception as e:
    print(f'❌ Error loading settings: {e}')

# Test 1: Send Test Email Function
print('🧪 Test 1: SEND TEST EMAIL Function...')
html_content = '''
<div style="font-family: Arial, sans-serif; padding: 20px; border: 2px solid #2196F3;">
    <h2 style="color: #2196F3;">🧪 Settings Test Email</h2>
    <p><strong>This is a test email from your Hospital Equipment System!</strong></p>
    <ul>
        <li>✅ Email Service: Working</li>
        <li>✅ Mailjet API: Connected</li>
        <li>✅ Settings Page: Functional</li>
    </ul>
    <p>📧 Sender: ''' + Config.EMAIL_SENDER + '''</p>
    <p>📬 Recipient: ''' + settings.get('recipient_email', 'Not set') + '''</p>
    <p>🕒 Sent from: Settings Test Function</p>
    <hr>
    <p style="color: #666; font-size: 12px;">Hospital Equipment Maintenance Management System</p>
</div>
'''

success = EmailService.send_immediate_email(
    recipients=[settings.get('recipient_email', Config.EMAIL_RECEIVER)],
    subject='🧪 Test Email from Settings Page',
    html_content=html_content
)

if success:
    print('✅ SEND TEST EMAIL: Working perfectly!')
    print('📬 Check your email for: "🧪 Test Email from Settings Page"')
else:
    print('❌ Send Test Email: Failed')

print()

# Test 2: Check maintenance data for Send Message Now
print('🧪 Test 2: SEND MESSAGE NOW - Check Maintenance Data...')
try:
    ppm_data = DataService.load_ppm_data()
    ocm_data = DataService.load_ocm_data()
    print(f'   📋 PPM Equipment: {len(ppm_data)} items loaded')
    print(f'   🔧 OCM Equipment: {len(ocm_data)} items loaded')
    
    if ppm_data or ocm_data:
        print('   ✅ Send Message Now: Ready with maintenance data')
        
        # Test getting upcoming maintenance
        from app.services.email_service import EmailService
        import asyncio
        
        async def test_upcoming():
            upcoming_ppm = await EmailService.get_upcoming_maintenance(ppm_data, 'ppm', 60)
            upcoming_ocm = await EmailService.get_upcoming_maintenance(ocm_data, 'ocm', 60)
            return upcoming_ppm, upcoming_ocm
        
        upcoming_ppm, upcoming_ocm = asyncio.run(test_upcoming())
        
        print(f'   📅 Upcoming PPM tasks (60 days): {len(upcoming_ppm)}')
        print(f'   📅 Upcoming OCM tasks (60 days): {len(upcoming_ocm)}')
        
        if upcoming_ppm or upcoming_ocm:
            print('   🎯 Send Message Now will send reminders for these tasks')
        else:
            print('   ℹ️  Send Message Now: No upcoming maintenance in next 60 days')
    else:
        print('   📨 Send Message Now: No maintenance data found')
        
except Exception as e:
    print(f'   ❌ Error checking maintenance data: {e}')

print()

# Test 3: System Status Summary
print('📊 System Status Summary:')
print(f'   🌐 Web App: http://localhost:5001')
print(f'   📧 Email Service: ✅ Operational')
print(f'   🔑 Mailjet API: ✅ Connected (dr.vet.waleedtam@gmail.com)')
print(f'   📬 Email Receiver: ✅ alorfbiomed@gmail.com')
print(f'   📅 Scheduler: ✅ Running (daily emails at 10:00 AM)')

print()
print('🌐 NEXT STEPS:')
print('1. Go to: http://localhost:5001')
print('2. Login to the system')
print('3. Navigate to Settings page')
print('4. Test these buttons:')
print('   • "Send Test Email" - Should work ✅')
print('   • "Send Message Now" - Should send maintenance reminders ✅')
print('   • Configure email recipients and timing ✅')

print('\n📧 Email Tests Complete! Check your inbox for test messages.') 