import pandas as pd
import pytest

from virtual_columns import core, eval_based


@pytest.fixture(params=[core, eval_based], ids=["core", "eval_based"])
def add_virtual_column(request):
    return request.param.add_virtual_column


def test_sum_of_two_columns(add_virtual_column):
    df = pd.DataFrame([[1, 1]] * 2, columns=["label_one", "label_two"])
    df_expected = pd.DataFrame([[1, 1, 2]] * 2, columns=["label_one", "label_two", "label_three"])
    df_result = add_virtual_column(df, "label_one+label_two", "label_three")
    assert df_result.equals(df_expected)


def test_multiplication_of_two_columns(add_virtual_column):
    df = pd.DataFrame([[1, 1]] * 2, columns=["label_one", "label_two"])
    df_expected = pd.DataFrame([[1, 1, 1]] * 2, columns=["label_one", "label_two", "label_three"])
    df_result = add_virtual_column(df, "label_one * label_two", "label_three")
    assert df_result.equals(df_expected)


def test_subtraction_of_two_columns(add_virtual_column):
    df = pd.DataFrame([[1, 1]] * 2, columns=["label_one", "label_two"])
    df_expected = pd.DataFrame([[1, 1, 0]] * 2, columns=["label_one", "label_two", "label_three"])
    df_result = add_virtual_column(df, "label_one - label_two", "label_three")
    assert df_result.equals(df_expected)


def test_empty_result_when_invalid_labels(add_virtual_column):
    df = pd.DataFrame([[1, 2]] * 3, columns=["label_one", "label_two"])
    assert add_virtual_column(df, "label_one + label_two", "label3").empty
    df = pd.DataFrame([[1, 2]] * 3, columns=["label-one", "label_two"])
    assert add_virtual_column(df, "label-one + label_two", "label").empty
    assert add_virtual_column(df, "label_one + label_two", "label").empty


def test_empty_result_when_invalid_rules(add_virtual_column):
    df = pd.DataFrame([[1, 1]] * 2, columns=["label_one", "label_two"])
    assert add_virtual_column(df, "label_one \\ label_two", "label_three").empty
    assert add_virtual_column(df, "label&one + label_two", "label_three").empty
    assert add_virtual_column(df, "label_five + label_two", "label_three").empty


def test_example_from_task(add_virtual_column):
    df = pd.DataFrame({"name": ["banana", "apple"], "quantity": [10, 3], "price": [10, 1]})
    result = add_virtual_column(df, "quantity * price", "total")
    assert result["total"].tolist() == [100, 3]
    assert "total" not in df.columns


def test_operator_precedence(add_virtual_column):
    df = pd.DataFrame({"a": [2], "b": [3], "c": [4]})
    assert add_virtual_column(df, "a + b * c", "r")["r"].tolist() == [14]
    assert add_virtual_column(df, "a - b - c", "r")["r"].tolist() == [-5]
    assert add_virtual_column(df, "a * b - c * a", "r")["r"].tolist() == [-2]


def test_python_keywords_as_labels():
    df = pd.DataFrame({"and": [1], "if": [2], "True": [3], "None": [4]})
    result = core.add_virtual_column(df, "and + if * True - None", "lambda")
    assert result["lambda"].tolist() == [3]


def test_eval_based_returns_empty_for_keyword_labels():
    df = pd.DataFrame({"and": [1], "b": [2]})
    assert eval_based.add_virtual_column(df, "and + b", "r").empty


def test_malformed_roles(add_virtual_column):
    df = pd.DataFrame({"a": [1], "b": [2]})
    for role in ["", "   ", "a +", "+ a", "a + + b", "a b", "a ** b", "(a + b)", "a / b", "a + 1"]:
        assert add_virtual_column(df, role, "r").empty, role


def test_invalid_inputs(add_virtual_column):
    df = pd.DataFrame({"a": [1], "b": [2]})
    assert add_virtual_column(df, None, "r").empty
    assert add_virtual_column(df, "a + b", None).empty
    assert add_virtual_column(None, "a + b", "r").empty
    assert add_virtual_column(pd.DataFrame([[1, 2]], columns=["a", "a"]), "a + a", "r").empty
    assert add_virtual_column(pd.DataFrame([[1, 2]], columns=[0, 1]), "a + b", "r").empty


def test_non_numeric_columns(add_virtual_column):
    df = pd.DataFrame({"a": ["x"], "b": ["y"], "n": [None]})
    assert add_virtual_column(df, "a * b", "r").empty
    assert add_virtual_column(df, "a - b", "r").empty
