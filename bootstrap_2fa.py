#!/usr/bin/env python3
"""One-time 2-step verification setup for the Synology MCP server.

Run this yourself in a terminal (it asks for a code, so it is not for a
scheduler):

    venv/bin/python bootstrap_2fa.py

It logs in with the account in .env plus a 6-digit code from your
authenticator app, asks DSM to trust this device, and writes the returned
SYNOLOGY_DEVICE_ID into .env. After that the server logs in without a code.
Run it again only if DSM stops accepting the token (for example after the
trusted device is removed in DSM > Personal > Security).
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / '.env')

from auth.synology_auth import SynologyAuth  # noqa: E402
from config import SynologyConfig  # noqa: E402


def main() -> int:
    config = SynologyConfig(env_file=str(ROOT / '.env'))
    errors = config.validate_config()
    if errors:
        print("Fix .env first: " + "; ".join(errors))
        return 1

    print(f"NAS:     {config.synology_url}")
    print(f"Account: {config.synology_username}")
    code = input("6-digit code from your authenticator app: ").strip().replace(' ', '')
    if not (code.isdigit() and len(code) == 6):
        print("That is not a 6-digit code. Nothing changed.")
        return 1

    auth = SynologyAuth(config.synology_url)
    result = auth.login(config.synology_username, config.synology_password, otp_code=code)
    if not result.get('success'):
        code_ = result.get('error', {}).get('code')
        hint = {400: "wrong username or password",
                403: "code rejected or expired; wait for the next code and retry",
                404: "code rejected; check the authenticator entry for this NAS"}.get(code_, "")
        print(f"Login failed (DSM error {code_}{': ' + hint if hint else ''}). Nothing changed.")
        return 1

    did = auth.current_device_id
    auth.logout()
    if not did:
        print("Logged in, but DSM did not issue a trusted-device token. Nothing changed.")
        return 1

    config.save_device_id(did)
    print("Saved SYNOLOGY_DEVICE_ID to .env. The MCP server will now log in without a code.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
