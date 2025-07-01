#!/usr/bin/env python3
"""
Setup script for Hospital Equipment System Email and Push Notification Configuration

This script helps configure:
1. Email settings (SMTP or Mailjet)
2. Push notification settings (VAPID keys)
3. Test the configuration
"""

import os
import secrets
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import base64
import json

def generate_vapid_keys():
    """Generate VAPID key pair for push notifications compatible with pywebpush."""
    print("🔑 Generating VAPID keys for push notifications...")

    # Generate private key
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    # Get public key
    public_key = private_key.public_key()

    # Serialize private key in DER format (not PEM) for pywebpush compatibility
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key in DER format
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Convert to base64url for web push (pywebpush expects this format)
    private_key_b64 = base64.urlsafe_b64encode(private_der).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_der).decode('utf-8').rstrip('=')

    return private_key_b64, public_key_b64

def create_env_file():
    """Create or update .env file with configuration."""
    env_content = []
    
    print("\n🏥 Hospital Equipment System Configuration Setup")
    print("=" * 50)
    
    # Email Configuration
    print("\n📧 EMAIL CONFIGURATION")
    print("Choose your email service:")
    print("1. Mailjet API (recommended - you're currently using this)")
    print("2. Gmail SMTP (alternative)")
    print("3. Skip email configuration")
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        print("\n📮 Mailjet API Configuration")
        print("Get your API credentials from: https://app.mailjet.com/account/api_keys")
        
        api_key = input("Mailjet API Key: ").strip()
        secret_key = input("Mailjet Secret Key: ").strip()
        sender = input("Sender email (verified in Mailjet): ").strip()
        receiver = input("Default receiver email: ").strip()
        
        env_content.extend([
            f"MAILJET_API_KEY={api_key}",
            f"MAILJET_SECRET_KEY={secret_key}",
            f"EMAIL_SENDER={sender}",
            f"EMAIL_RECEIVER={receiver}"
        ])
        
    elif choice == "2":
        print("\n📮 Gmail SMTP Configuration")
        print("Note: You'll need to use an App Password, not your regular Gmail password")
        print("Instructions: https://support.google.com/accounts/answer/185833")
        
        email = input("Gmail address: ").strip()
        password = input("App Password (not your regular password): ").strip()
        sender = input(f"Sender name [{email}]: ").strip() or email
        receiver = input("Default receiver email: ").strip()
        
        env_content.extend([
            f"MAIL_USERNAME={email}",
            f"MAIL_PASSWORD={password}",
            f"MAIL_DEFAULT_SENDER={sender}",
            f"EMAIL_SENDER={sender}",
            f"EMAIL_RECEIVER={receiver}",
            "MAIL_SERVER=smtp.gmail.com",
            "MAIL_PORT=587",
            "MAIL_USE_TLS=true"
        ])
    
    # Push Notification Configuration
    print("\n🔔 PUSH NOTIFICATION CONFIGURATION")
    generate_vapid = input("Generate VAPID keys for push notifications? (y/n): ").strip().lower()
    
    if generate_vapid == 'y':
        try:
            private_key, public_key = generate_vapid_keys()
            vapid_subject = input("VAPID Subject (your email for contact): ").strip() or "mailto:admin@yourdomain.com"
            env_content.extend([
                f"VAPID_PRIVATE_KEY={private_key}",
                f"VAPID_PUBLIC_KEY={public_key}",
                f"VAPID_SUBJECT={vapid_subject}"
            ])
            print("✅ VAPID keys generated successfully!")
        except Exception as e:
            print(f"❌ Failed to generate VAPID keys: {e}")
            print("You can skip this and configure push notifications later.")
    
    # Flask Configuration
    env_content.extend([
        "FLASK_ENV=development",
        "FLASK_DEBUG=1",
        "SCHEDULER_ENABLED=true"
    ])
    
    # Write .env file
    if env_content:
        with open('.env', 'w') as f:
            f.write('\n'.join(env_content))
        
        print(f"\n✅ Configuration saved to .env file!")
        print("\n📋 Your .env file contains:")
        for line in env_content:
            if 'PASSWORD' in line or 'SECRET' in line or 'PRIVATE_KEY' in line:
                key = line.split('=')[0]
                print(f"   {key}=***")
            else:
                print(f"   {line}")
    
    return len(env_content) > 0

def test_email_config():
    """Test email configuration."""
    print("\n📧 Testing Email Configuration...")
    
    try:
        # Import after potential .env creation
        from app.config import Config
        from app.services.email_service import EmailService
        
        # Test email content
        test_subject = "Hospital Equipment System - Test Email"
        test_content = """
        <html>
        <body>
            <h2>🏥 Hospital Equipment System</h2>
            <p>This is a test email to verify your email configuration is working correctly.</p>
            <p>If you received this email, your email settings are properly configured!</p>
            <hr>
            <p><small>Generated by setup script</small></p>
        </body>
        </html>
        """
        
        # Get test recipient
        test_email = input("Enter email address to send test email to: ").strip()
        if not test_email:
            print("❌ No email address provided. Skipping email test.")
            return False
        
        # Send test email
        print("📤 Sending test email...")
        success = EmailService.send_immediate_email([test_email], test_subject, test_content)
        
        if success:
            print("✅ Test email sent successfully!")
            print(f"📬 Check {test_email} for the test message.")
            return True
        else:
            print("❌ Failed to send test email.")
            print("💡 Check your email configuration and try again.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email: {e}")
        return False

def main():
    """Main setup function."""
    print("🏥 Hospital Equipment System Setup")
    print("This script will help you configure email and push notifications.")
    print("\nPress Ctrl+C at any time to exit.")
    
    try:
        # Create configuration
        config_created = create_env_file()
        
        if config_created:
            print("\n🔄 Reloading environment variables...")
            
            # Load .env file manually
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
            
            # Test email configuration
            test_email = input("\nTest email configuration now? (y/n): ").strip().lower()
            if test_email == 'y':
                test_email_config()
        
        print("\n🎉 Setup complete!")
        print("\n📝 Next steps:")
        print("1. Restart your Flask application to load new environment variables")
        print("2. Test the email and push notification features in the settings page")
        print("3. Configure recipient emails in the application settings")
        
        print("\n🚀 To start the application:")
        print("   python -m flask run -p 5001 --debug")
        
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")

if __name__ == "__main__":
    main() 