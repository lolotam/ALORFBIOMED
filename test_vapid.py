#!/usr/bin/env python3
"""Test VAPID configuration loading"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== VAPID Configuration Test ===")
print(f"VAPID_PRIVATE_KEY: {os.environ.get('VAPID_PRIVATE_KEY', 'NOT SET')[:50]}...")
print(f"VAPID_PUBLIC_KEY: {os.environ.get('VAPID_PUBLIC_KEY', 'NOT SET')[:50]}...")
print(f"VAPID_SUBJECT: {os.environ.get('VAPID_SUBJECT', 'NOT SET')}")

# Test if the subject has mailto: prefix
vapid_subject = os.environ.get('VAPID_SUBJECT', 'mailto:dr.vet.waledmohamed@gmail.com')
print(f"Final VAPID_SUBJECT: {vapid_subject}")
print(f"Has mailto: prefix: {vapid_subject.startswith('mailto:')}")
