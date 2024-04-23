import os
from collections import defaultdict
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class FootwearType(Enum):
    SHOES = "s"
    BOOTS = "b"
    UNSHOD = "u"
    OTHER = "o"


class FootwearSubtype(Enum):
    MINIMAL = "mn"
    BAREFOOT = "b"
    SOCKED = "s"
    MEDICAL = "md"
    UNSHOD = "u"
    REGULAR = ""
    MIXED = "bs"


class SizeType(Enum):
    MENS = "m"
    WOMENS = "w"
    YOUTH = "y"


class Dtypes(Enum):
    CATEGORY = "category"
    DATETIME = "datetime64[s]"
    FLOAT = "float"
    INT = "int"
    STR = "str"


class Config:
    EXPORT_DIR = Path(os.environ.get("EXPORT_DIR", "."))

    PROJECT_DIR = Path(__file__).parents[2]
    CRED_DIR = PROJECT_DIR / ".cred"
    CRED_FILE = CRED_DIR / "credentials.json"
    TOKEN_FILE = CRED_DIR / "token.json"
    BACKUP_CSV = PROJECT_DIR / "data" / "raw" / "data.csv"
    DB_FILE = PROJECT_DIR / "data" / "processed" / "data.db"

    # If modifying these scopes, delete the file token.json.
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    # The ID and range of a sample spreadsheet.
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    WORKSHEET_NAME = "IMPFDcurrent"

    FONT = "Arial"
    JSAR_FONT_SIZE = 10

    # Colors
    BRAND_PRIMARY = "#3E552B"
    BRAND_SECONDARY = "#EDDEBF"

    FOOTWEAR_COLOR = {
        "boots": "#82B756",
        "unshod": "#826868",
        "minimal": "#C3AC77",
        "shoes": "#6475B3",
        "mixed": "#BF6E85",
    }
    FOOTWEAR_MARKER = {
        "boots": "circle",
        "shoes": "square",
        "unshod": "circle-open-dot",
        "minimal": "diamond-wide",
        "mixed": "cross",
    }

    SIZE_TOLERANCE = 0.5

    ID_COL = "DBnum"
    COUNT = "Count"
    PERC = "Percent"
    MIXED = "Mixed"
    SIZE = "Size"
    # Sections
    SECTION = "Section"
    ADMIN = "ADMINISTRATIVE"
    REPORTED = "REPORTED"
    FOUND = "FOUND"
    SEPARATE = "SEPARATE"
    # Columns
    ID = "ID"
    BRAND = "Brand"
    COLOR = "Color"
    COUNTRY = "Country"
    DATE = "Date"
    LPB = "LPB"
    SIZE = "Size"
    SIZE_LO = "Size_Lo"
    SIZE_HI = "Size_Hi"
    SIZE_TYPE = "SizeType"
    STATE = "State"
    SUBTYPE = "Subtype"
    TYPE = "Type"
    DIST_LO = "Dist_Lo"
    DIST_HI = "Dist_Hi"

    COLUMNS = {
        ADMIN: {
            "DBnum": {"rename": ID, "dtype": Dtypes.INT},
            "Source": None,
            "caseID": None,
            "Loc": None,
            "State": {"rename": STATE, "dtype": Dtypes.CATEGORY},
            "Country": {"rename": COUNTRY, "dtype": Dtypes.CATEGORY},
            "Ccode": None,
            "CScode": None,
            "Snum": None,
            "DBcode": None,
            "Date": {"rename": DATE, "dtype": Dtypes.DATETIME},
            "LPB": {"rename": LPB, "dtype": Dtypes.CATEGORY},
            "Evasive": None,
        },
        REPORTED: {
            "RepType": {"rename": TYPE, "dtype": Dtypes.CATEGORY},
            "RepSub": {"rename": SUBTYPE, "dtype": Dtypes.CATEGORY},
            "RepColor": {"rename": COLOR, "dtype": Dtypes.STR},
            "Mco": None,
            "RepBrand": {"rename": BRAND, "dtype": Dtypes.CATEGORY},
            "RepSizeLo": {"rename": SIZE_LO, "dtype": Dtypes.FLOAT},
            "RepSizeHi": {"rename": SIZE_HI, "dtype": Dtypes.FLOAT},
            "RepSizeRa": None,
            "rMWY": {"rename": SIZE_TYPE, "dtype": Dtypes.CATEGORY},
            "RepSUSwide": None,
            "RepAltTy": None,
            "RepAltCo": None,
            "RepAltBr": None,
            "RepAdd": None,
        },
        FOUND: {
            "FoundType": {"rename": TYPE, "dtype": Dtypes.CATEGORY},
            "FoundSub": {"rename": SUBTYPE, "dtype": Dtypes.CATEGORY},
            "FoundColor": {"rename": COLOR, "dtype": Dtypes.STR},
            "FoundBrand": {"rename": BRAND, "dtype": Dtypes.CATEGORY},
            "FoundSize": {"rename": SIZE_LO, "dtype": Dtypes.FLOAT},
            "fMWY": {"rename": SIZE_TYPE, "dtype": Dtypes.CATEGORY},
            "FoundWidth": None,
            "FoundAdd": None,
        },
        SEPARATE: {
            "Removal": None,
            "FFoff": None,
            "SepDistClose": {"rename": DIST_LO, "dtype": Dtypes.FLOAT},
            "SepDistFar": {"rename": DIST_HI, "dtype": Dtypes.FLOAT},
            "SepType": {"rename": TYPE, "dtype": Dtypes.CATEGORY},
            "SepSub": {"rename": SUBTYPE, "dtype": Dtypes.CATEGORY},
            "SepColor": {"rename": COLOR, "dtype": Dtypes.STR},
            "SepBrand": {"rename": BRAND, "dtype": Dtypes.CATEGORY},
            "SepSize": {"rename": SIZE_LO, "dtype": Dtypes.FLOAT},
            "SepMWY": {"rename": SIZE_TYPE, "dtype": Dtypes.CATEGORY},
        },
    }

    DTYPES: dict[str, dict] = defaultdict(dict)
    for section in COLUMNS:
        for value in COLUMNS[section].values():
            if value is None:
                continue
            DTYPES[section][value["rename"]] = {k: v for k, v in value.items() if k != "rename"}
