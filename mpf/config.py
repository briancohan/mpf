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
    BACKUP_CSV = PROJECT_DIR / "data.csv"

    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    WORKSHEET_NAME = os.getenv("WORKSHEET_NAME")

    # Colors
    BRAND_PRIMARY = "#3E552B"
    BRAND_SECONDARY = "#EDDEBF"

    FOOTWEAR_COLOR = dict(
        boots="#82B756",
        unshod="#826868",
        minimal="#C3AC77",
        shoes="#6475B3",
        mix="#BF6E85",
    )

    # Keywords
    REPORTED = "REPORTED"
    FOUND = "FOUND"
    COUNT = "Count"
    MATCH = "Match"
    NA = "N/A"

    ID = "Identifier"
    LOCATION = "Location"
    STATE = "State"
    DATE = "Date"
    LPB = "LPB"

    TYPE = "Type"
    COLOR = "Color"
    BRAND = "Brand"
    SIZE = "Size"
    SIZE_CAT = "m/w/y"
    WIDTH = "Width"

    METRICS = [
        TYPE,
        COLOR,
        SIZE,
        BRAND,
        # WIDTH,
    ]

    REPORT = "Report Type"
    METRIC = "Data Metric"
