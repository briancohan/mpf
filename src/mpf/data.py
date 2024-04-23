from enum import EnumType
from itertools import zip_longest
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mpf import graph
from mpf.config import Config, FootwearSubtype, FootwearType, SizeType


########################################
# General Utilities
########################################
# MARK: create_column_index
def create_column_index(lvl0: list[str], lvl1: list[str]) -> pd.MultiIndex:
    """Create a multi-level column index from two lists of strings.

    lvl0 should be the first row in the Google Sheet, and lvl1 should be the second row.
    If lvl0 is blank, it will use the last non-blank value.
    """
    _lvl0 = []
    last = ""
    for col in lvl0:
        last = col or last
        _lvl0.append(last)

    return pd.MultiIndex.from_tuples(zip_longest(_lvl0, lvl1, fillvalue=_lvl0[-1]))


########################################
# Fetch Data
########################################
# MARK: get_latest_data
def get_latest_data(
    *,
    creds: dict,
    workbook: str | None,
    ws_range: str,
) -> pd.DataFrame:
    """Fetch latest data from Google Sheets. If fails, load from backup CSV.

    After pulling the data from Google Sheets, the following transformations are performed:
    - Combine the first two rows to create a multi-level column index
    - Replace empty strings with NaN
    """
    service = build("sheets", "v4", credentials=creds)

    try:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=workbook, range=ws_range).execute()
        values = result.get("values", [])

    except HttpError:
        return pd.DataFrame()

    df = pd.DataFrame(
        columns=create_column_index(values[0], values[1]),
        data=values[2:],
    )
    df = df.fillna(np.nan).replace("", np.nan)

    return df


# MARK: get_backup_data
def get_backup_data(backup_csv: Path = Config.BACKUP_CSV) -> pd.DataFrame:
    """Load data from backup CSV."""
    return pd.read_csv(backup_csv, header=[0, 1]).replace("", np.nan).fillna(np.nan)


# MARK: get_data
def get_data(
    creds: dict,
    workbook: str | None = Config.SPREADSHEET_ID,
    ws_range: str = Config.WORKSHEET_NAME,
    backup_csv: Path = Config.BACKUP_CSV,
) -> pd.DataFrame:
    """Get latest data from Google Sheets. If fails, load from backup CSV.

    Will automatically store the latest data in the backup CSV.
    """
    df = get_latest_data(creds=creds, workbook=workbook, ws_range=ws_range)

    if not df.empty:
        df.to_csv(backup_csv)
        return df

    return get_backup_data(backup_csv)


########################################
# Import Helpers
########################################
# MARK: _fix_dtypes
def _fix_dtypes(df: pd.DataFrame, cols: dict) -> pd.DataFrame:
    """Fix the dtypes of the dataframe."""
    for info in cols.values():
        df[info["rename"]] = df[info["rename"]].astype(info["dtype"].value, errors="ignore")

    return df


# MARK: fix_missing_size_hi
def _fix_missing_size_hi(df: pd.DataFrame) -> pd.DataFrame:
    """Fill in missing size_hi values with size_lo."""
    if Config.SIZE_HI not in df.columns:
        df[Config.SIZE_HI] = df[Config.SIZE_LO]
    else:
        df[Config.SIZE_HI] = df[Config.SIZE_HI].fillna(df[Config.SIZE_LO])

    df[Config.SIZE_HI] = df[Config.SIZE_HI].astype(float)
    return df


# MARK: _drop_empty_records
def _drop_empty_records(df: pd.DataFrame) -> pd.DataFrame:
    """Drop records that are empty."""
    return df.dropna(how="all")


# MARK: _decode_category_column
def _decode_category_column(
    df: pd.DataFrame,
    col: str,
    enum: EnumType,
) -> pd.DataFrame:
    """Decode a column.

    Some columns have one or two character codes to indicate a value. Enums are defined in the
    config file to decode these values. This function will decode the values and replace them with.
    """
    df[col] = df[col].astype(str)
    entry: Any
    for entry in enum:
        df.loc[df[col] == entry.value, col] = entry.name.title()

    return df


# MARK: _normalize_section
def _normalize_section(df: pd.DataFrame, section: str) -> pd.DataFrame:
    """Normalize the section of the dataframe."""
    cols = {k: v for k, v in Config.COLUMNS[section].items() if v is not None}

    # Get the columns that are needed
    _df = df[section].copy()
    _df = _df.rename(columns={k: v["rename"] for k, v in cols.items()})
    _df = _df[[v["rename"] for v in cols.values()]]

    # Clean up the table
    _df = _drop_empty_records(_df)
    _df = _fix_missing_size_hi(_df)

    # Add the section and ID column from admin section
    _df[Config.SECTION] = section
    _df[Config.ID] = df[(Config.ADMIN, Config.ID_COL)].astype(int)

    _df = _fix_dtypes(_df, cols)
    return _df


########################################
# Usuable Data
########################################
# MARK: create_admin_table
def create_admin_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create table of just the admin data.

    Will raise an error if an ID has different associated values.
    """
    _df = df[Config.ADMIN].copy()

    # Rename columns and drop any columns that are not needed
    cols = {k: v for k, v in Config.COLUMNS[Config.ADMIN].items() if v is not None}
    _df = _df.rename(columns={k: v["rename"] for k, v in cols.items()})
    _df = _df[[v["rename"] for v in cols.values()]]

    # Clean up remaining table
    _df = _df.drop_duplicates()
    _df = _df.reset_index(drop=True)
    _df = _fix_dtypes(_df, cols)

    if not _df[Config.ID].is_unique:
        raise ValueError("ID is not unique, admin data likely not properly duplicated")

    return _df


# MARK: create_footwear_table
def create_footwear_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a table with all the footwear data."""
    _df = pd.concat(
        [
            _normalize_section(df, Config.REPORTED),
            _normalize_section(df, Config.FOUND),
            _normalize_section(df, Config.SEPARATE),
        ]
    )

    _df = _decode_category_column(_df, Config.TYPE, FootwearType)
    _df = _decode_category_column(_df, Config.SUBTYPE, FootwearSubtype)
    _df = _decode_category_column(_df, Config.SIZE_TYPE, SizeType)

    return _df


########################################
# Reported vs Found Correctness
########################################
# MARK: correct_type
def correct_type(reported: str, found: str) -> bool:
    if not isinstance(found, str):
        return False

    return reported.lower() == found.lower()


# MARK: correct_brand
def correct_brand(reported: str, found: str) -> bool:
    if not isinstance(found, str):
        return False

    return reported.lower() == found.lower()


# MARK: correct_size
def correct_size(
    reported: tuple[float, float],
    found: tuple[float, float],
    tolerance: float = Config.SIZE_TOLERANCE,
) -> bool:
    if len(found) != 2:
        raise ValueError("Found size must be a tuple of length 2")
    if found[0] == np.nan:
        return False

    return reported[0] - tolerance <= found[0] <= reported[1] + tolerance


# MARK: correct_color
def correct_color(reported: str, found: str) -> bool:
    if not isinstance(found, str):
        return False

    return bool(set(reported.lower().split("/")) & set(found.lower().split("/")))


# MARK: _correct_x_summary
def _correct_x_summary(
    footwear: pd.DataFrame,
    *,
    col: str,
    func: Callable,
    fillna: str | float,
    sep_as_found: bool,
) -> pd.DataFrame:
    """Summary of x correctness."""
    _df = footwear.copy()
    if sep_as_found:
        _df = graph.utils.fix_separate_as_found(_df)

    _df = _df[[Config.ID, Config.SECTION, col]].replace("nan", np.nan).dropna()

    f_df = (
        _df[_df[Config.SECTION].isin([Config.REPORTED, Config.FOUND])]
        .pivot_table(
            index=Config.ID,
            columns=Config.SECTION,
            values=col,
            aggfunc="first",
        )
        .dropna()
    )
    f_df["Correct"] = f_df.apply(lambda x: func(x[Config.REPORTED], x[Config.FOUND]), axis=1)
    summary = [
        {
            "Metric": col,
            "Report": Config.FOUND,
            "Correct": f_df["Correct"].sum(),
            "Incorrect": len(f_df) - f_df["Correct"].sum(),
        }
    ]

    if sep_as_found:
        return summary

    s_df = (
        _df[_df[Config.SECTION].isin([Config.REPORTED, Config.SEPARATE])]
        .pivot_table(
            index=Config.ID,
            columns=Config.SECTION,
            values=col,
            aggfunc="first",
        )
        .dropna()
    )
    s_df["Correct"] = s_df.apply(lambda x: func(x[Config.REPORTED], x[Config.SEPARATE]), axis=1)
    summary.append(
        {
            "Metric": col,
            "Report": Config.SEPARATE,
            "Correct": s_df["Correct"].sum(),
            "Incorrect": len(s_df) - s_df["Correct"].sum(),
        }
    )

    return summary


# MARK: correct_brand_summary
def correct_brand_summary(footwear: pd.DataFrame) -> pd.DataFrame:
    """Summary of brand correctness."""
    return _correct_x_summary(
        footwear,
        col=Config.BRAND,
        func=correct_brand,
        fillna="<nan>",
        sep_as_found=True,
    )


# MARK: correct_color_summary
def correct_color_summary(footwear: pd.DataFrame) -> pd.DataFrame:
    """Summary of color correctness."""
    return _correct_x_summary(
        footwear,
        col=Config.COLOR,
        func=correct_color,
        fillna="<nan>",
        sep_as_found=True,
    )


# MARK: correct_type_summary
def correct_type_summary(footwear: pd.DataFrame) -> pd.DataFrame:
    """Summary of type correctness."""
    return _correct_x_summary(
        footwear,
        col=Config.TYPE,
        func=correct_type,
        fillna="",
        sep_as_found=False,
    )


# MARK: correct_size_summary
def correct_size_summary(footwear: pd.DataFrame) -> pd.DataFrame:
    """Summary of size correctness."""
    _df = footwear.copy()
    _df = _df[[Config.ID, Config.SECTION, Config.SIZE_LO, Config.SIZE_HI]]
    _df = _df.dropna(subset=[Config.SIZE_LO])
    _df[Config.SIZE] = _df[[Config.SIZE_LO, Config.SIZE_HI]].values.tolist()
    _df.loc[_df[Config.SECTION] == Config.FOUND, Config.SIZE]

    return _correct_x_summary(
        _df,
        col=Config.SIZE,
        func=correct_size,
        fillna=0,
        sep_as_found=True,
    )
