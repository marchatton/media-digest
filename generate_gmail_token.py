#!/usr/bin/env python3
"""Generate Gmail OAuth token."""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    # Point to your downloaded credentials file
    creds_path = input("Enter path to downloaded credentials JSON file: ").strip()
    
    if not os.path.exists(creds_path):
        print(f"Error: {creds_path} not found!")
        return
    
    # Generate new token
    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Save the token
    token_path = 'gmail_token.json'
    with open(token_path, 'w') as token:
        token.write(creds.to_json())
    
    print(f"\nToken saved to {token_path}")
    print(f"\nNow upload to Hetzner with:")
    print(f"scp -i ~/.ssh/hetzner_media_digest gmail_token.json root@46.62.207.244:/opt/digestor/secure/")

if __name__ == '__main__':
    main()
