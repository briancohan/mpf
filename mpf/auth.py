from __future__ import print_function

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Config


def get_credentials() -> dict:
    creds = None

    if Config.TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(Config.TOKEN_FILE, Config.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                Config.CRED_FILE,
                Config.SCOPES,
            )
            creds = flow.run_local_server(port=0)

        Config.TOKEN_FILE.write_text(creds.to_json())

    return creds
