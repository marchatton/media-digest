#!/usr/bin/env python3
"""Generate Gmail OAuth token."""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_DIR = Path('secure')
TOKEN_PATH = TOKEN_DIR / 'gmail_token.json'


def main() -> None:
    creds_path_input = input("Enter path to downloaded credentials JSON file: ").strip()
    creds_path = Path(creds_path_input)

    if not creds_path.exists():
        print(f"Error: {creds_path} not found!")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())

    print(f"\nToken saved to {TOKEN_PATH}")
    print("\nNow upload to Hetzner with:")
    print(
        "scp -i ~/.ssh/hetzner_media_digest secure/gmail_token.json "
        "root@46.62.207.244:/opt/digestor/secure/"
    )


if __name__ == '__main__':
    main()
