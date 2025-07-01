#!/usr/bin/env python3
"""
Fix VAPID keys for push notifications.
"""

import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def generate_vapid_keys():
    """Generate new VAPID keys"""
    print("🔑 Generating new VAPID keys...")
    
    try:
        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        
        # Get private key in DER format
        private_der = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key in DER format
        public_key = private_key.public_key()
        public_der = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Encode to base64
        private_key_b64 = base64.b64encode(private_der).decode('utf-8')
        public_key_b64 = base64.b64encode(public_der).decode('utf-8')
        
        print(f"✅ Private key generated: {len(private_key_b64)} characters")
        print(f"✅ Public key generated: {len(public_key_b64)} characters")
        
        return private_key_b64, public_key_b64
        
    except Exception as e:
        print(f"❌ Error generating VAPID keys: {e}")
        return None, None

def update_env_file():
    """Update the .env22 file with new VAPID keys"""
    print("\n📝 Updating .env22 file...")
    
    private_key, public_key = generate_vapid_keys()
    
    if not private_key or not public_key:
        print("❌ Failed to generate VAPID keys")
        return False
    
    try:
        # Read current .env22 file
        env_file = ".env22"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Update VAPID keys
        updated_lines = []
        vapid_private_updated = False
        vapid_public_updated = False
        
        for line in lines:
            if line.startswith('VAPID_PRIVATE_KEY='):
                updated_lines.append(f'VAPID_PRIVATE_KEY={private_key}\n')
                vapid_private_updated = True
            elif line.startswith('VAPID_PUBLIC_KEY='):
                updated_lines.append(f'VAPID_PUBLIC_KEY={public_key}\n')
                vapid_public_updated = True
            else:
                updated_lines.append(line)
        
        # Add missing keys if not found
        if not vapid_private_updated:
            updated_lines.append(f'VAPID_PRIVATE_KEY={private_key}\n')
        if not vapid_public_updated:
            updated_lines.append(f'VAPID_PUBLIC_KEY={public_key}\n')
        
        # Write updated file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated {env_file} with new VAPID keys")
        
        # Also update environment variables for current session
        os.environ['VAPID_PRIVATE_KEY'] = private_key
        os.environ['VAPID_PUBLIC_KEY'] = public_key
        
        print("✅ Updated environment variables for current session")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env22 file: {e}")
        return False

def test_vapid_keys():
    """Test the new VAPID keys"""
    print("\n🧪 Testing new VAPID keys...")
    
    try:
        private_key_b64 = os.environ.get('VAPID_PRIVATE_KEY')
        public_key_b64 = os.environ.get('VAPID_PUBLIC_KEY')
        
        if not private_key_b64 or not public_key_b64:
            print("❌ VAPID keys not found in environment")
            return False
        
        # Test private key deserialization
        private_der = base64.b64decode(private_key_b64)
        private_key = serialization.load_der_private_key(
            private_der, 
            password=None, 
            backend=default_backend()
        )
        
        # Test public key deserialization
        public_der = base64.b64decode(public_key_b64)
        public_key = serialization.load_der_public_key(
            public_der, 
            backend=default_backend()
        )
        
        print("✅ Private key deserialization: SUCCESS")
        print("✅ Public key deserialization: SUCCESS")
        print(f"✅ Private key type: {type(private_key).__name__}")
        print(f"✅ Public key type: {type(public_key).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ VAPID key test failed: {e}")
        return False

def main():
    """Fix VAPID keys"""
    print("🔧 VAPID Keys Fix Utility")
    print("=" * 50)
    
    print("Current VAPID keys status:")
    current_private = os.environ.get('VAPID_PRIVATE_KEY', 'Not set')
    current_public = os.environ.get('VAPID_PUBLIC_KEY', 'Not set')
    
    print(f"Private key length: {len(current_private) if current_private != 'Not set' else 0}")
    print(f"Public key length: {len(current_public) if current_public != 'Not set' else 0}")
    
    # Update with new keys
    if update_env_file():
        print("\n🎉 VAPID keys updated successfully!")
        
        # Test the new keys
        if test_vapid_keys():
            print("\n✅ VAPID keys are working correctly!")
            print("\n💡 NEXT STEPS:")
            print("1. Restart the Flask application to load new keys")
            print("2. Test push notifications from the settings page")
            print("3. The push notification test should now work")
            return True
        else:
            print("\n❌ VAPID key test failed")
            return False
    else:
        print("\n❌ Failed to update VAPID keys")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
