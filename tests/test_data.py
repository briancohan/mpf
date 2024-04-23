import numpy as np
import pandas as pd
import pytest
from mpf import data
from mpf.config import Config


# MARK: create_column_index
def test_create_column_index() -> None:
    """
    Ensure multi-index is created correctly.

    When the first row has empty cells (merged cells), the multi-index should copy the value until
    the next non-empty cell.
    """
    l0 = ["a", "", "b", ""]
    l1 = ["1", "2", "3", "4", "5"]
    ix = data.create_column_index(l0, l1)

    expected = pd.MultiIndex.from_tuples(
        [
            ("a", "1"),
            ("a", "2"),
            ("b", "3"),
            ("b", "4"),
            ("b", "5"),
        ]
    )

    assert np.array_equal(ix.values, expected)


# MARK: correct_type
@pytest.mark.parametrize(
    argnames=["reported", "found", "expected"],
    argvalues=[
        ("Shoes", "Unshod", False),
        ("Shoes", "Shoes", True),
        ("Shoes", "shoes", True),
        ("Shoes", np.nan, False),
    ],
)
def test_correct_type(
    reported: str,
    found: str,
    expected: bool,
) -> None:
    """
    Ensure correct type matches.

    Values are considered equal if they are the same. Case insensitive.
    """
    result = data.correct_type(reported, found)
    assert result == expected


# MARK: correct_brand
@pytest.mark.parametrize(
    argnames=["reported", "found", "expected"],
    argvalues=[
        ("NIKE", "nike", True),
        ("Nike", "nike", True),
        ("nike", "nike", True),
        ("nike", "crocs", False),
        ("nike", np.nan, False),
    ],
)
def test_correct_brand(
    reported: str,
    found: str,
    expected: bool,
) -> None:
    """
    Ensure correct brand matches.

    Values are considered equal if they are the same. Case insensitive.
    """
    result = data.correct_brand(reported, found)
    assert result == expected


# MARK: correct_size
@pytest.mark.parametrize(
    argnames=["reported", "found", "tolerance", "expected"],
    argvalues=[
        ([5.0, 6.0], [4.5, 4.5], 0.0, False),
        ([5.0, 6.0], [5.0, 5.0], 0.0, True),
        ([5.0, 6.0], [5.5, 5.5], 0.0, True),
        ([5.0, 6.0], [6.0, 6.0], 0.0, True),
        ([5.0, 6.0], [6.5, 6.5], 0.0, False),
        ([5.0, 6.0], [6.5, 6.5], 0.5, True),
    ],
)
def test_correct_size(
    reported: tuple[float, float],
    found: tuple[float, float],
    tolerance: float,
    expected: bool,
) -> None:
    """
    Ensure correct size matches.

    Found tuple should be the same number for both positions. This stems from concatenating
    SIZE_LO and SIZE_HI regardless of reported or found.

    If the found is within the bounds of the reported size +- the tolerance,
    the match should be True.
    """
    result = data.correct_size(reported, found, tolerance=tolerance)
    assert result == expected


# MARK: correct_color
@pytest.mark.parametrize(
    argnames=["reported", "found", "expected"],
    argvalues=[
        ("black/white", "black/white", True),
        ("black/white", "black", True),
        ("black/white", "white", True),
        ("black/white", "orange", False),
        ("brown", "tan", False),
        ("black", "black", True),
        ("black", np.nan, False),
    ],
)
def test_correct_color(
    reported: str,
    found: str,
    expected: bool,
) -> None:
    """
    Ensure correct color matches.

    If the reported and found values are the same, the match should be True.
    """
    result = data.correct_color(reported, found)
    assert result == expected


# MARK: _build_dataframe
def _build_dataframe(reports: list[dict[str, str]], *, col: str) -> pd.DataFrame:
    data = [
        {Config.ID: ix, Config.SECTION: section, col: report[section]}
        for ix, report in enumerate(reports)
        for section in [Config.REPORTED, Config.FOUND, Config.SEPARATE]
        if section in report
    ]

    return pd.DataFrame(data)


# MARK: test_build_dataframe
def test_build_dataframe() -> None:
    result_df = _build_dataframe(
        reports=[
            {Config.REPORTED: "Shoes", Config.FOUND: "Shoes"},
            {Config.REPORTED: "Shoes", Config.FOUND: "Boots"},
            {Config.REPORTED: "Boots", Config.FOUND: "Boots"},
        ],
        col=Config.TYPE,
    )
    expected_df = pd.DataFrame(
        [
            {Config.ID: 0, Config.SECTION: Config.REPORTED, Config.TYPE: "Shoes"},
            {Config.ID: 0, Config.SECTION: Config.FOUND, Config.TYPE: "Shoes"},
            {Config.ID: 1, Config.SECTION: Config.REPORTED, Config.TYPE: "Shoes"},
            {Config.ID: 1, Config.SECTION: Config.FOUND, Config.TYPE: "Boots"},
            {Config.ID: 2, Config.SECTION: Config.REPORTED, Config.TYPE: "Boots"},
            {Config.ID: 2, Config.SECTION: Config.FOUND, Config.TYPE: "Boots"},
        ]
    )

    assert result_df.shape == (6, 3)
    assert result_df.equals(expected_df)


# MARK: test_correct_type_summary
def test_correct_type_summary() -> None:
    df = _build_dataframe(
        reports=[
            {Config.REPORTED: "Shoes", Config.FOUND: "Shoes"},
            {Config.REPORTED: "Shoes", Config.FOUND: "Boots"},
            {Config.REPORTED: "Boots", Config.FOUND: "Boots"},
        ],
        col=Config.TYPE,
    )

    summary = data.correct_type_summary(df)
    assert summary[0]["Correct"] == 2
    assert summary[0]["Incorrect"] == 1


# MARK: test_correct_brand_summary
def test_correct_brand_summary() -> None:
    df = _build_dataframe(
        reports=[
            {Config.REPORTED: "nike", Config.FOUND: "nike"},
            {Config.REPORTED: "nike", Config.FOUND: "croc"},
            {Config.REPORTED: "croc", Config.FOUND: "croc"},
        ],
        col=Config.BRAND,
    )

    summary = data.correct_brand_summary(df)
    assert summary[0]["Correct"] == 2
    assert summary[0]["Incorrect"] == 1


# MARK: test_correct_size_summary
def test_correct_color_summary() -> None:
    df = _build_dataframe(
        reports=[
            {Config.REPORTED: "black/white", Config.FOUND: "black/white"},
            {Config.REPORTED: "black/white", Config.FOUND: "black"},
            {Config.REPORTED: "black/white", Config.FOUND: "white"},
            {Config.REPORTED: "black/white", Config.FOUND: "orange"},
            {Config.REPORTED: "brown", Config.FOUND: "tan"},
            {Config.REPORTED: "black", Config.FOUND: "black"},
        ],
        col=Config.COLOR,
    )

    summary = data.correct_color_summary(df)
    assert summary[0]["Correct"] == 4
    assert summary[0]["Incorrect"] == 2
