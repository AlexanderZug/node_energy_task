import calendar
import csv
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from dateutil import parser

from exeptions import InsufficientDataError


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

    def get_dates(self) -> list[str]:
        dates = []
        for value in self.get_meter_values():
            dates.append(value["date"])
        return sorted(dates, key=lambda date: parser.parse(date))

    def check_sufficient_data_available_in_the_past(self) -> None:
        first_date = parser.parse(self.get_dates()[0])
        if first_date.month == self.month and first_date.day != 1:
            raise InsufficientDataError()

    def check_sufficient_data_available_in_the_future(self) -> None:
        last_date = parser.parse(self.get_dates()[-1])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        if last_date.month == self.month and last_date.day != days_in_month:
            raise InsufficientDataError()

    def get_base_price(self) -> Decimal:
        base_tariff = Decimal(self.get_customer()[0]["base_tariff"])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        base_price = base_tariff / Decimal(365) * Decimal(days_in_month)
        return base_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    def get_days_difference(
        self, first_date: parser.parse, second_date: parser.parse
    ) -> int:
        return abs((first_date - second_date).days)

    def get_energy_price(self):
        # energy_tariff = Decimal(self.get_customer()[0]["energy_tariff"])

        dates = self.get_dates()
        meter_values = self.get_meter_values()

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
                * int(current_value_dict["value"])
            )
            days_difference2 = Decimal(
                (
                    calendar.monthrange(current_date.year, current_date.month)[1]
                    - current_date.day
                )
                / self.get_days_difference(current_date, next_date)
                * int(current_value_dict["value"])
            )

            print(
                days_difference2.quantize(Decimal("0.01"), rounding=ROUND_DOWN),
                days_difference1.quantize(Decimal("0.01"), rounding=ROUND_DOWN),
            )

    @staticmethod
    def read_csv(file_path) -> list[dict]:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File {file_path} not found.")
        with Path.open(file_path, newline="") as csvfile:
            return list(csv.DictReader(csvfile))
