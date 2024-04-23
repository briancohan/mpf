"""
Module to handle authentication with Google Sheets API.

Code adapted from Google Sheets API Quickstart guide:
https://developers.google.com/sheets/api/quickstart/python#configure_the_sample
"""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Config


def get_credentials(
    token_file: Path = Config.TOKEN_FILE,
    cred_file: Path = Config.CRED_FILE,
    scopes: list[str] = Config.SCOPES,
) -> Credentials:
    """Get valid credentials for Google Sheets API."""
    creds = None

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(token_file, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_file, scopes)
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json())

    return creds
