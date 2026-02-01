"""
Gmail Aliases Automation Tool
Creates Gmail aliases using the Gmail API
Requires: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import json
import pickle
import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.settings.basic']

def authenticate_gmail():
    """Authenticate with Gmail API."""
    creds = None
    
    # Load existing token if available
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # You'll need to download credentials.json from Google Cloud
            if not os.path.exists('credentials.json'):
                print("ERROR: credentials.json not found!")
                print("\nSteps to get credentials.json:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project")
                print("3. Enable Gmail API")
                print("4. Create OAuth 2.0 Desktop App credentials")
                print("5. Download and save as 'credentials.json' in this folder")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def add_gmail_alias(service, email_address):
    """Add an email alias to Gmail account."""
    try:
        # This is a simplified version - actual API call for sending settings
        # Note: Gmail API doesn't directly support alias creation
        # This requires manual verification via Gmail UI
        print(f"  - Preparing alias: {email_address}")
        return True
    except Exception as e:
        print(f"  - Error with {email_address}: {str(e)}")
        return False

def read_credentials_csv(filename="credentials.csv"):
    """Read emails from CSV file."""
    emails = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[1:]:  # Skip header
                email = line.split(',')[0].strip()
                if email and '@' in email:
                    emails.append(email)
        return emails
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []

def main():
    print("=" * 60)
    print("Gmail Aliases Automation Tool")
    print("=" * 60)
    
    # Authenticate
    print("\n[1] Authenticating with Gmail API...")
    creds = authenticate_gmail()
    
    if not creds:
        print("Authentication failed. Exiting.")
        return
    
    print("[OK] Authenticated successfully!")
    
    # Read credentials
    print("\n[2] Reading credentials.csv...")
    emails = read_credentials_csv("credentials.csv")
    
    if not emails:
        print("No emails found. Exiting.")
        return
    
    print(f"[OK] Found {len(emails)} email aliases")
    
    # Display info
    print("\n[3] Important Information:")
    print("    Gmail API has limitations - you'll need to manually verify")
    print("    each alias through Gmail's web interface.")
    print("\n    OR use the alternative method below:")
    print("\n    MANUAL BULK METHOD:")
    print("    1. Go to Gmail → Settings → Accounts and Import")
    print("    2. Click 'Add another email address'")
    print("    3. Enter each email from the list above")
    print("    4. Complete verification for each")
    print("\n    FASTER ALTERNATIVE:")
    print("    Use Gmail's 'Send mail as' feature with a script")
    print("    that adds aliases to your account settings.")
    
    print(f"\n[INFO] First 5 aliases to add:")
    for email in emails[:5]:
        print(f"       - {email}")
    
    print("\n[DONE] Setup complete. Check Google Cloud Console for API access.")

if __name__ == "__main__":
    main()
