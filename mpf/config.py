import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    EXPORT_DIR = Path(os.environ.get("EXPORT_DIR", "."))

    PROJECT_DIR = Path(__file__).parents[1]
    CRED_DIR = PROJECT_DIR / "cred"
    CRED_FILE = next(CRED_DIR.glob("*.json"))
    TOKEN_FILE = CRED_DIR / "token.json"

    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

    BRAND_PRIMARY = "#3E552B"
    BRAND_SECONDARY = "#EDDEBF"
