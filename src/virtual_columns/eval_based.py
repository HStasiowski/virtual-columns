"""Short alternative to core.py: same validation, but DataFrame.eval does the maths."""

import re

import pandas

LABEL = re.compile(r"[A-Za-z_]+")
ROLE = re.compile(r"\s*[A-Za-z_]+\s*(?:[-+*]\s*[A-Za-z_]+\s*)*")


def _is_valid_label(label) -> bool:
    return isinstance(label, str) and LABEL.fullmatch(label) is not None


def add_virtual_column(df: pandas.DataFrame, role: str, new_column: str) -> pandas.DataFrame:
    if not isinstance(df, pandas.DataFrame) or not isinstance(role, str):
        return pandas.DataFrame([])
    if not _is_valid_label(new_column) or ROLE.fullmatch(role) is None:
        return pandas.DataFrame([])
    if not all(_is_valid_label(c) for c in df.columns) or not df.columns.is_unique:
        return pandas.DataFrame([])
    if any(label not in df.columns for label in LABEL.findall(role)):
        return pandas.DataFrame([])

    try:
        # The regex above guarantees only column names and + - * reach eval.
        # Python keywords as column names (and, if, ...) make eval fail -> empty result.
        values = df.eval(role)
    except Exception:
        return pandas.DataFrame([])

    result = df.copy()
    result[new_column] = values
    return result
