# 📧 Mailjet Email Configuration Guide

Since you're using Mailjet, here's the specific setup for your Hospital Equipment System:

## 🚀 **Quick Mailjet Setup**

### **Step 1: Get Your Mailjet Credentials**

1. **Login to Mailjet:** https://app.mailjet.com/
2. **Go to API Keys:** Account Settings → REST API → API Key Management
3. **Copy your credentials:**
   - API Key (Primary)
   - Secret Key (Primary)

### **Step 2: Configure Your System**

**Option A: Run the Setup Script (Recommended)**
```bash
python setup_email_config.py
```
- Choose option 1 (Mailjet API)
- Enter your API credentials
- Enter your verified sender email

**Option B: Manual Configuration**

Edit your `.env` file:
```env
# Mailjet Configuration
MAILJET_API_KEY=your-api-key-here
MAILJET_SECRET_KEY=your-secret-key-here
EMAIL_SENDER=your-verified-sender@domain.com
EMAIL_RECEIVER=alorfbiomed@gmail.com

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SCHEDULER_ENABLED=true

# Push Notifications (optional)
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_SUBJECT=mailto:your-email@domain.com
```

### **Step 3: Verify Sender Email**

🚨 **Important:** Your sender email must be verified in Mailjet:

1. **Go to:** Account Settings → Sender Addresses
2. **Add your sender email** if not already added
3. **Verify** through the confirmation email
4. **Wait for approval** (usually instant for free accounts)

### **Step 4: Test Your Configuration**

1. **Restart your Flask server:**
   ```bash
   # Stop current server (Ctrl+C)
   python -m flask run -p 5001 --debug
   ```

2. **Test in the application:**
   - Go to: http://localhost:5001/settings
   - Click **"Send Test Email"** ✅ Should work now
   - Click **"Send Message Now"** ✅ Should send actual reminders

## 🔧 **Troubleshooting**

### **"Failed to send test email"**
- ✅ Check your API keys are correct
- ✅ Verify sender email is verified in Mailjet
- ✅ Check recipient email is valid
- ✅ Look at application logs for detailed errors

### **"0 emails sent" for Send Message Now**
- ✅ Verify Mailjet configuration is complete
- ✅ Check that email notifications are enabled in settings
- ✅ Ensure recipient emails are configured

### **Push notification errors**
- ✅ Generate VAPID keys using the setup script
- ✅ Make sure VAPID_SUBJECT is set

## 📊 **Current Settings from Logs**

I can see your current settings are:
```json
{
  "email_notifications_enabled": true,
  "recipient_email": "alorfbiomed@gmail.com",
  "cc_emails": "lolotam@gmail.com",
  "use_daily_send_time": true,
  "email_send_time": "09:15",
  "enable_automatic_reminders": true
}
```

## ✅ **What Should Work Now**

After configuring Mailjet:
- ✅ **Send Test Email** button will work
- ✅ **Send Message Now** will send to `alorfbiomed@gmail.com` 
- ✅ **CC emails** will go to `lolotam@gmail.com`
- ✅ **Daily emails** scheduled for 9:15 AM
- ✅ **Backup downloads** working
- ✅ **Settings persistence** working

## 🎯 **Next Steps**

1. **Configure Mailjet API keys** (most important)
2. **Test email functionality**
3. **Configure push notifications** (optional)
4. **Set up production monitoring**

Your system found **122 PPM tasks** that need maintenance - once Mailjet is configured, these reminder emails will be sent automatically! 🎉 