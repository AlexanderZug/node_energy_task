from pathlib import Path
from unittest.mock import patch

import pytest

from src import cli
from src.invoice import Invoice


@pytest.fixture()
def fixtures_path() -> Path:
    path = Path(__file__).parent.parent
    return path / "fixtures"


def test_get_cli_options() -> None:
    args = [
        "--id",
        "12345",
        "-y",
        "2021",
        "-m",
        "7",
        "--customer-file",
        "customers.csv",
        "--values-file",
        "values.csv",
    ]
    with patch("sys.argv", [cli.__file__, *args]):
        options = cli.get_cli_options()

    assert options.id == "12345"
    assert options.year == 2021
    assert options.month == 7
    assert options.customer_file == "customers.csv"
    assert options.values_file == "values.csv"


def test_can_find_customer_with_id(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "customers.csv"
    invoice = Invoice("12345", 2021, 7, fixtures_file, "values.csv")
    customer = invoice.get_customer()
    assert len(customer) == 1
    assert customer[0]["id"] == "12345"


def test_raises_error_if_customer_not_found(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "customers.csv"
    invoice = Invoice("54321", 2021, 7, fixtures_file, "values.csv")
    with pytest.raises(ValueError) as ex:
        invoice.check_customer_exists()
    assert str(ex.value) == "Customer with id 54321 not found."


def test_can_find_meter_values_for_customer(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    values = invoice.get_meter_values()
    assert len(values) == 4
    assert values[0]["date"] == "2021-03-02"
    assert values[1]["customer"] == "12345"
    assert values[2]["value"] == "100"


def test_raises_error_if_date_not_found(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2025, 7, "customers.csv", fixtures_file)
    with pytest.raises(ValueError) as ex:
        invoice.check_date_exists()
    assert str(ex.value) == "Date with month 7 and year 2025 not found."


def test_can_sort_dates(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_dates()
    assert dates == [
        "2021-02-08",
        "2021-03-02",
        "2021-03-30",
        "2021-04-27",
    ]


def test_can_check_sufficient_data_available_in_the_past(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 1, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_dates()
    with pytest.raises(ValueError):
        invoice.check_sufficient_data_available_in_the_past(dates)


def test_can_check_sufficient_data_available_in_the_future(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_dates()
    with pytest.raises(ValueError):
        invoice.check_sufficient_data_available_in_the_future(dates)


def test_can_check_sufficient_data_available(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_dates()
    with pytest.raises(ValueError) as ex:
        invoice.check_sufficient_data_available(dates)
    assert str(ex.value) == "Not sufficient data available"
