import re
from functools import reduce
from operator import mul

import pandas

LABEL = re.compile(r"[A-Za-z_]+")
ROLE = re.compile(r"\s*[A-Za-z_]+\s*(?:[-+*]\s*[A-Za-z_]+\s*)*")
TOKEN = re.compile(r"[A-Za-z_]+|[-+*]")


def _is_valid_label(label) -> bool:
    return isinstance(label, str) and LABEL.fullmatch(label) is not None


def _evaluate(df: pandas.DataFrame, role: str) -> pandas.Series:
    # Grammar: expr = term (('+' | '-') term)*, term = label ('*' label)*.
    # Splitting into multiplicative terms first gives '*' precedence over '+' and '-'.
    tokens = TOKEN.findall(role)
    terms, signs, current = [], [1], [tokens[0]]
    for op, label in zip(tokens[1::2], tokens[2::2], strict=True):
        if op == "*":
            current.append(label)
        else:
            terms.append(current)
            signs.append(1 if op == "+" else -1)
            current = [label]
    terms.append(current)

    result = None
    for sign, term in zip(signs, terms, strict=True):
        value = reduce(mul, (df[label] for label in term))
        if result is None:
            result = value if sign == 1 else -value
        else:
            result = result + value if sign == 1 else result - value
    return result


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
        values = _evaluate(df, role)
    except Exception:
        # e.g. unsupported operations on non-numeric columns
        return pandas.DataFrame([])

    result = df.copy()
    result[new_column] = values
    return result
