from statistics import mean

import numpy as np
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import Config


########################################
# General Utilities
########################################
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

        df = pd.DataFrame(values[2:], columns=create_column_index(values[0], values[1]))
        df = df.replace("", np.nan).fillna(np.nan)

        df.fillna("").to_csv(Config.BACKUP_CSV)

    except HttpError:
        print("LOADING FROM BACKUP")
        df = pd.read_csv(Config.BACKUP_CSV, header=[0, 1]).replace("", np.nan).fillna(np.nan)

    return df


def get_value_counts(df: pd.DataFrame, col: str, dropna: bool = True) -> pd.DataFrame:
    _df = (
        df.iloc[:, df.columns.get_level_values(1) == col].value_counts(dropna=dropna).reset_index()
    )
    _df.columns = [col, Config.COUNT]
    return _df


def column_comparison(df: pd.DataFrame, columns: str | list[str]) -> pd.DataFrame:
    if isinstance(columns, str):
        columns = [columns]

    _df = df.iloc[:, df.columns.get_level_values(1).isin(columns)]
    if len(columns) == 1:
        _df.columns = _df.columns.get_level_values(0)
    return _df


def column_comparison_no_na(df: pd.DataFrame, col: str, keep_type: bool = True) -> pd.DataFrame:
    _df = column_comparison(df, [Config.TYPE, col]).dropna(
        subset=[(Config.REPORTED, col), (Config.FOUND, col)],
    )

    for col_ in [Config.TYPE, col]:
        _df[("MATCH", col_)] = _df[(Config.REPORTED, col_)] == _df[(Config.FOUND, col_)]

    if not keep_type:
        _df = _df.iloc[:, [1, 3, 5]]
        _df.columns = _df.columns.get_level_values(0)

    return _df


########################################
# Data Extraction
########################################
def high_level_stats(df: pd.DataFrame) -> dict:
    data = {}
    data["How Many Subjects"] = len(df)  # Assuming each record is a new subject

    _df = get_value_counts(df, Config.ID)
    _df = _df[_df[Config.ID] != ""]
    data["How Many Missions"] = len(_df)

    for subjects, count in _df.Count.value_counts().to_dict().items():
        data[f"How many searches with {subjects} subject(s)"] = count

    return data


def clean_shoe_size_data(df: pd.DataFrame) -> pd.DataFrame:
    _df = (
        column_comparison(df, [Config.TYPE, Config.SIZE, Config.SIZE_CAT])
        .replace("", np.nan)
        .fillna(np.nan)
    )

    rdf = _df.loc[:, Config.REPORTED].dropna(how="all", subset=[Config.SIZE, Config.SIZE_CAT])
    rdf["Report"] = Config.REPORTED

    fdf = _df.loc[:, Config.FOUND].dropna(how="all", subset=[Config.SIZE, Config.SIZE_CAT])
    fdf["Report"] = Config.FOUND

    _df = pd.concat([rdf, fdf])
    _df[Config.SIZE] = [mean([float(i) for i in r.split("-")]) for r in _df[Config.SIZE]]
    _df = _df[~_df[Config.TYPE].isna()]
    _df[Config.SIZE_CAT] = _df[Config.SIZE_CAT].fillna("o")

    return _df
