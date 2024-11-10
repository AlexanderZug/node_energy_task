import calendar
import csv
from datetime import datetime
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from dateutil import parser

from src.exeptions import InsufficientDataError


class Invoice:
    def __init__(self, customer_id: str, year: int, month: int) -> None:
        self.customer_id = customer_id
        self.year = year
        self.month = month

    def get_customer(self) -> list[dict[str, str]]:
        customers = self.read_csv("data/customers.csv")
        return [
            customer for customer in customers if customer["id"] == self.customer_id
        ]

    def get_meter_values(self) -> list[dict[str, str]]:
        meter_values = self.read_csv("data/meter_values.csv")
        return [row for row in meter_values if row["customer"] == self.customer_id]

    def check_customer_exists(self) -> None:
        if not self.get_customer():
            raise ValueError(f"Customer with id {self.customer_id} not found.")

    def check_date_exists(self) -> None:
        for value in self.get_meter_values():
            if (
                not parser.parse(value["date"]).year == self.year
                and parser.parse(value["date"]).month == self.month
            ):
                raise ValueError(f"Date {value['date']} not found.")

    def get_sorted_dates(self) -> list[str]:
        dates = []
        for value in self.get_meter_values():
            dates.append(value["date"])
        return sorted(dates, key=lambda date: parser.parse(date))

    def check_sufficient_data_available_in_the_past(self) -> None:
        first_date = parser.parse(self.get_sorted_dates()[0])
        if first_date.month == self.month and first_date.day != 1:
            raise InsufficientDataError()

    def check_sufficient_data_available_in_the_future(self) -> None:
        last_date = parser.parse(self.get_sorted_dates()[-1])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        if last_date.month == self.month and last_date.day != days_in_month:
            raise InsufficientDataError()

    def get_base_price(self) -> Decimal:
        base_tariff = Decimal(self.get_customer()[0]["base_tariff"])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        base_price = base_tariff / Decimal(365) * Decimal(days_in_month)
        return base_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    def get_energy_price(self) -> Decimal:
        energy_tariff = Decimal(self.get_customer()[0]["energy_tariff"])
        share_period = [
            item
            for item in self.get_share_period()
            if parser.parse(item["date"]).month == self.month
        ]
        energy_price = share_period[0]["value"] * (energy_tariff / Decimal(100))
        return energy_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    def get_share_period(self):
        dates = self.get_sorted_dates()
        meter_values = self.get_meter_values()
        share_period = []

        for key, date in enumerate(dates):
            if key == 0 or key == len(dates) - 1:
                continue

            current_date = parser.parse(date)
            previous_date = parser.parse(dates[key - 1])
            next_date = parser.parse(dates[key + 1])

            current_value_dict = next(
                (
                    value
                    for value in meter_values
                    if parser.parse(value["date"]) == current_date
                ),
                None,
            )

            days_difference1 = Decimal(
                current_date.day
                / self.get_days_difference(current_date, previous_date)
                * float(current_value_dict["value"])
            )
            days_difference2 = Decimal(
                (
                    calendar.monthrange(current_date.year, current_date.month)[1]
                    - current_date.day
                )
                / self.get_days_difference(current_date, next_date)
                * float(current_value_dict["value"])
            )

            share_period.append(
                {"date": date, "value": days_difference1 + days_difference2}
            )
        return share_period

    @staticmethod
    def get_days_difference(first_date: datetime, second_date: datetime) -> int:
        return abs((first_date - second_date).days)

    @staticmethod
    def read_csv(file_path: str) -> list[dict[str, str]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")
        with path.open(newline="") as csvfile:
            return list(csv.DictReader(csvfile))
