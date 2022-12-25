import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .auth import get_credentials
from .config import Config


def create_column_index(lvl0: list, lvl1: list) -> pd.MultiIndex:
    l0 = []
    last = lvl0[0]
    for ix in range(len(lvl1)):
        try:
            current = lvl0[ix]
        except IndexError:
            current = ""

        if not current:
            current = last

        l0.append(current)
        last = current

    return pd.MultiIndex.from_tuples(zip(l0, lvl1))


def get_data(creds: dict) -> pd.DataFrame:
    service = build("sheets", "v4", credentials=creds)

    try:
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(
                spreadsheetId=Config.SPREADSHEET_ID,
                range=Config.WORKSHEET_NAME,
            )
            .execute()
        )
        values = result.get("values", [])

    except HttpError as err:
        print(err)

    df = pd.DataFrame(values[2:], columns=create_column_index(values[0], values[1]))
    return df


def get_value_counts(df: pd.DataFrame, col: str) -> pd.DataFrame:
    _df = df.iloc[:, df.columns.get_level_values(1) == col].value_counts().reset_index()
    _df.columns = [col, "Count"]
    return _df


if __name__ == "__main__":
    creds = get_credentials()
    df = get_data(creds=creds)
    print(df)
