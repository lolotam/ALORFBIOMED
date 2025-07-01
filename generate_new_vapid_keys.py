#!/usr/bin/env python3
"""
Generate new VAPID keys for push notifications.
"""

import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from py_vapid import Vapid

def generate_vapid_keys():
    """Generate new VAPID keys using cryptography library"""
    print("🔑 Generating New VAPID Keys")
    print("=" * 50)
    
    # Generate a new private key using the P-256 curve (required for VAPID)
    print("📝 Generating EC private key (P-256 curve)...")
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # Get the public key
    public_key = private_key.public_key()
    
    # Serialize private key to DER format
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to DER format
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

def test_vapid_keys(private_key_b64, public_key_b64):
    """Test the generated VAPID keys"""
    print(f"\n🧪 Testing Generated VAPID Keys")
    print("-" * 40)
    
    # Test 1: py_vapid compatibility
    try:
        vapid_obj = Vapid.from_string(private_key=private_key_b64)
        print(f"✅ py_vapid.Vapid.from_string: SUCCESS")
        
        # Get public key from private key
        derived_public_key = vapid_obj.public_key
        print(f"✅ Public key derivation: SUCCESS")
        
    except Exception as e:
        print(f"❌ py_vapid test FAILED: {e}")
        return False
    
    # Test 2: Cryptography library compatibility
    try:
        private_der = base64.b64decode(private_key_b64)
        public_der = base64.b64decode(public_key_b64)
        
        # Load private key
        private_key = serialization.load_der_private_key(
            private_der, 
            password=None, 
            backend=default_backend()
        )
        
        # Load public key
        public_key = serialization.load_der_public_key(
            public_der, 
            backend=default_backend()
        )
        
        print(f"✅ Cryptography library: SUCCESS")
        print(f"✅ Private key type: {type(private_key).__name__}")
        print(f"✅ Public key type: {type(public_key).__name__}")
        print(f"✅ Curve: {private_key.curve.name}")
        
    except Exception as e:
        print(f"❌ Cryptography test FAILED: {e}")
        return False
    
    # Test 3: pywebpush compatibility
    try:
        from pywebpush import webpush
        
        # Create a dummy subscription for testing
        test_subscription = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test",
            "keys": {
                "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
                "auth": "tBHItJI5svbpez7KI4CCXg"
            }
        }
        
        # This should fail with network error, but not VAPID key error
        try:
            webpush(
                subscription_info=test_subscription,
                data="test",
                vapid_private_key=private_key_b64,
                vapid_claims={"sub": "mailto:test@example.com"}
            )
            print(f"✅ pywebpush: SUCCESS (unexpected)")
        except Exception as e:
            error_msg = str(e).lower()
            if 'asn.1' in error_msg or 'deserialize' in error_msg or 'vapid' in error_msg:
                print(f"❌ pywebpush VAPID error: {e}")
                return False
            else:
                print(f"✅ pywebpush: VAPID keys accepted (network error: {type(e).__name__})")
                
    except Exception as e:
        print(f"❌ pywebpush test FAILED: {e}")
        return False
    
    print(f"✅ All tests passed!")
    return True

def update_env_file(private_key_b64, public_key_b64):
    """Update the .env22 file with new VAPID keys"""
    print(f"\n📝 Updating .env22 File")
    print("-" * 30)
    
    env_file = ".env22"
    
    try:
        # Read current file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update VAPID keys
        updated_lines = []
        private_updated = False
        public_updated = False
        
        for line in lines:
            if line.startswith('VAPID_PRIVATE_KEY='):
                updated_lines.append(f'VAPID_PRIVATE_KEY={private_key_b64}\n')
                private_updated = True
                print(f"✅ Updated VAPID_PRIVATE_KEY")
            elif line.startswith('VAPID_PUBLIC_KEY='):
                updated_lines.append(f'VAPID_PUBLIC_KEY={public_key_b64}\n')
                public_updated = True
                print(f"✅ Updated VAPID_PUBLIC_KEY")
            else:
                updated_lines.append(line)
        
        # Add keys if they weren't found
        if not private_updated:
            updated_lines.append(f'VAPID_PRIVATE_KEY={private_key_b64}\n')
            print(f"✅ Added VAPID_PRIVATE_KEY")
        
        if not public_updated:
            updated_lines.append(f'VAPID_PUBLIC_KEY={public_key_b64}\n')
            print(f"✅ Added VAPID_PUBLIC_KEY")
        
        # Write updated file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ {env_file} updated successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update {env_file}: {e}")
        return False

def main():
    """Main function"""
    print("🏥 Hospital Equipment System - VAPID Key Generator")
    print("=" * 70)
    
    # Generate new keys
    private_key_b64, public_key_b64 = generate_vapid_keys()
    
    # Test the keys
    if not test_vapid_keys(private_key_b64, public_key_b64):
        print("\n❌ Generated keys failed testing!")
        return False
    
    # Update .env22 file
    if not update_env_file(private_key_b64, public_key_b64):
        print("\n❌ Failed to update environment file!")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 NEW VAPID KEYS GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"✅ Keys are properly formatted and tested")
    print(f"✅ .env22 file updated with new keys")
    print(f"✅ Keys are compatible with pywebpush library")
    
    print(f"\n📋 New VAPID Keys:")
    print(f"Private Key: {private_key_b64}")
    print(f"Public Key:  {public_key_b64}")
    
    print(f"\n🔄 NEXT STEPS:")
    print(f"1. Restart the Flask application to load new keys")
    print(f"2. Test push notifications in the settings page")
    print(f"3. Clear any existing push subscriptions if needed")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
