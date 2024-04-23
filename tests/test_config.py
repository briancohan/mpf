from mpf.config import Config


def test_data_column_operations() -> None:
    """
    Ensure columns are properly defined for injestion.

    Excluded columns should have a value of None.
    Included columns should have a dict containing 'rename' and 'dtype'.
    """
    for section in Config.COLUMNS:
        for value in Config.COLUMNS[section].values():
            if value is not None:
                assert "rename" in value
                assert "dtype" in value
