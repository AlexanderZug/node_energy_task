from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from src import cli
from src.invoice import Invoice


@pytest.fixture()
def fixtures_path() -> Path:
    path = Path(__file__).parent
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
        invoice.check_values_exist()
    assert str(ex.value) == "Date with month 7 and year 2025 not found."


def test_can_sort_dates(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_values()
    assert dates == [
        "2021-02-08",
        "2021-03-02",
        "2021-03-30",
        "2021-04-27",
    ]


def test_can_check_sufficient_data_available_in_the_past(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 1, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_values()
    with pytest.raises(ValueError):
        invoice.check_sufficient_data_available_in_the_past(dates)


def test_can_check_sufficient_data_available_in_the_future(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_values()
    with pytest.raises(ValueError):
        invoice.check_sufficient_data_available_in_the_future(dates)


def test_can_check_sufficient_data_available(fixtures_path: Path) -> None:
    fixtures_file = fixtures_path / "values.csv"
    invoice = Invoice("12345", 2021, 7, "customers.csv", fixtures_file)
    dates = invoice.get_sorted_values()
    with pytest.raises(ValueError) as ex:
        invoice.check_sufficient_data_available(dates)
    assert str(ex.value) == "Not sufficient data available"


@pytest.mark.parametrize(
    "year, month, expected_base_price",
    [
        (2020, 2, Decimal("11.10")),  # leap year
        (2021, 2, Decimal("10.74")),
        (2024, 2, Decimal("11.10")),  # leap year
        (2023, 7, Decimal("11.90")),
    ],
)
def test_base_price(
    fixtures_path: Path, year: int, month: int, expected_base_price: Decimal
) -> None:
    fixtures_file_customer = fixtures_path / "customers.csv"
    fixtures_file_values = fixtures_path / "values.csv"
    invoice = Invoice(
        "12345", year, month, fixtures_file_customer, fixtures_file_values
    )

    base_price = invoice.get_base_price()
    assert (
        base_price == expected_base_price
    ), f"Expected {expected_base_price}, got {base_price}"


@pytest.mark.parametrize(
    "year, month, customer_id, energy_tariff, expected_energy_price",
    [
        (
            2021,
            3,  # two values for this month
            "12345",
            "24.8",
            Decimal("28.52"),
        ),  # ((1 / 22 * 250) + (28 / 30 * 100) + (2 / 29 * 150)) * 24.8 / 100
        (
            2021,
            2,
            "6789",
            "20.0",
            Decimal("2163.40"),
        ),  # ((5 / 35 * 9052) + (23 / 40 * 16562)) * 20.0 / 100
        (
            2021,  # no values for this month (tree values)
            3,
            "9876",
            "19.2",
            Decimal("825.92"),
        ),  # (31 / 38 * 5273) * 19.2 / 100
        (
            2021,  # no values for this month (five values)
            6,
            "4567",
            "18.4",
            Decimal("59.68"),
        ),  # (30 / 37 * 400) * 18.4 / 100
    ],
)
def test_energy_price(
    fixtures_path: Path,
    year: int,
    month: int,
    customer_id: str,
    energy_tariff: str,
    expected_energy_price: Decimal,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures_file_customer = fixtures_path / "customers.csv"
    fixtures_file_values = fixtures_path / "values.csv"

    invoice = Invoice(
        customer_id, year, month, fixtures_file_customer, fixtures_file_values
    )

    monkeypatch.setattr(
        invoice, "get_customer", lambda: [{"energy_tariff": energy_tariff}]
    )
    invoice.get_energy_price()

    assert invoice.get_energy_price() == expected_energy_price


@pytest.mark.parametrize(
    "customer_id, year, month, expected_name, expected_street, expected_postcode, expected_city",
    [
        ("12345", 2021, 3, "Muster", "Teststrasse 0", "12345", "Teststadt"),
        ("6789", 2021, 2, "Adam", "Teststrasse2 7", "56789", "Teststadt2"),
        ("9876", 2021, 3, "Eva", "Teststrasse3 4", "19399", "Teststadt3"),
    ],
)
def test_make_report(
    fixtures_path: Path,
    tmp_path: Path,
    customer_id: str,
    year: int,
    month: int,
    expected_name: str,
    expected_street: str,
    expected_postcode: str,
    expected_city: str,
) -> None:
    temp_report_dir = tmp_path / "reports"
    temp_report_dir.mkdir()

    invoice = Invoice(
        customer_id,
        year,
        month,
        fixtures_path / "customers.csv",
        fixtures_path / "values.csv",
    )
    invoice.make_report(temp_report_dir)
    file_name = f"report_{invoice.customer_id}_{invoice.month}.txt"

    assert (temp_report_dir / file_name).exists()
    with (temp_report_dir / file_name).open() as file:
        report = file.readlines()

    assert expected_name in report[0]
    assert expected_street in report[1]
    assert f"{expected_postcode} {expected_city}" in report[2]
