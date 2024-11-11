import calendar
import csv
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from pathlib import Path

from dateutil import parser


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

    def check_sufficient_data_available(self, sorted_dates: list[str]) -> list[str]:
        try:
            sorted_dates = self.check_sufficient_data_available_in_the_past(
                sorted_dates
            )
            sorted_dates = self.check_sufficient_data_available_in_the_future(
                sorted_dates
            )
        except ValueError as ex:
            raise ValueError("Not sufficient data available") from ex
        return sorted_dates

    def check_sufficient_data_available_in_the_past(
        self, sorted_dates: list[str]
    ) -> list[str]:
        first_date = parser.parse(sorted_dates[0])
        if (
            first_date.month < self.month
            or first_date.month == self.month
            and first_date.day == 1
        ):
            return sorted_dates
        raise ValueError

    def check_sufficient_data_available_in_the_future(
        self, sorted_dates: list[str]
    ) -> list[str]:
        last_date = parser.parse(sorted_dates[-1])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        if last_date.month > self.month:
            return sorted_dates
        elif last_date.month == self.month and last_date.day == days_in_month:
            sorted_dates.append(sorted_dates[-1])
            return sorted_dates
        raise ValueError

    def get_base_price(self) -> Decimal:
        base_tariff = Decimal(self.get_customer()[0]["base_tariff"])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        base_price = base_tariff / Decimal(365) * Decimal(days_in_month)
        return base_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    def get_energy_price(self) -> Decimal:
        energy_tariff = Decimal(self.get_customer()[0]["energy_tariff"])
        consumptions = self.get_interval_consumption()
        share_period = [
            date
            for date in self.insert_missing_month(consumptions)
            if parser.parse(date["date"]).month == self.month
        ]

        energy_price = Decimal(share_period[-1]["value"]) * (
            energy_tariff / Decimal(100)
        )
        return energy_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

    def insert_missing_month(self, consumptions: list[dict]) -> list[dict]:
        for index in range(len(consumptions) - 1):
            current_date = parser.parse(consumptions[index]["date"])
            next_date = parser.parse(consumptions[index + 1]["date"])

            if current_date.month < self.month < next_date.month:
                new_date = datetime(self.year, self.month, 1)
                new_entry = {
                    "date": new_date.strftime("%Y-%m-%d"),
                    "value": Decimal(
                        calendar.monthrange(self.year, self.month)[1]
                        / self.get_days_difference(current_date, next_date)
                        * float(consumptions[index + 1]["value"])
                    ),
                }
                consumptions.insert(index + 1, new_entry)
                break
        return consumptions

    def get_interval_consumption(self) -> list[dict]:
        dates = self.check_sufficient_data_available(self.get_sorted_dates())
        meter_values = self.get_meter_values()
        share_period = []

        for index, date in enumerate(dates):
            if index == 0 or index == len(dates) - 1:
                continue

            current_date = parser.parse(date)
            previous_date = parser.parse(dates[index - 1])
            next_date = parser.parse(dates[index + 1])

            current_value_dict = next(
                (
                    value
                    for value in meter_values
                    if parser.parse(value["date"]) == current_date
                ),
            )

            next_value_dict = next(
                value
                for value in meter_values
                if parser.parse(value["date"]) == next_date
            )

            current_value = float(current_value_dict["value"])
            next_value = float(next_value_dict["value"])

            first_interval_consumption = Decimal(
                (current_date - timedelta(days=1)).day
                / self.get_days_difference(current_date, previous_date)
                * current_value
            )
            second_interval_consumption = Decimal(
                (
                    calendar.monthrange(current_date.year, current_date.month)[1]
                    - (current_date - timedelta(days=1)).day
                )
                / self.get_days_difference(current_date, next_date)
                * next_value
            )

            share_period.append(
                {
                    "date": date,
                    "value": (
                        first_interval_consumption + second_interval_consumption
                    ).quantize(Decimal("1"), rounding=ROUND_DOWN),
                }
            )
        return share_period

    def get_month_range(self) -> str:
        first_day = datetime(self.year, self.month, 1)

        last_day = calendar.monthrange(self.year, self.month)[1]
        last_day = datetime(self.year, self.month, last_day)

        return f"{first_day.strftime('%d.%m.%Y')} bis {last_day.strftime('%d.%m.%Y')}"

    def make_report(self):
        customer_info = self.get_customer()[0]
        customer_name = customer_info["name"]
        customer_street = customer_info["street"]
        customer_postcode = customer_info["postcode"]
        customer_city = customer_info["city"]
        period = self.get_month_range()
        base_price = self.get_base_price()
        energy_price = self.get_energy_price()
        total_price = base_price + energy_price

        report_lines = [
            f"{customer_name}",
            f"{customer_street}",
            f"{customer_postcode} {customer_city}",
            f"Abrechnungszeitraum {period}",
            "Komponente    Anzahl    Preis        Kosten",
            "----------------------------------------------",
            f"Grundpreis    30 Tage x 170.0 €/Jahr = {base_price:.2f} €",
            f"Arbeitspreis  1177 kWh x 23.2 ct/kWh = {energy_price:.2f} €",
            "----------------------------------------------",
            f"Summe        {total_price:.2f} €",
        ]

        with open("report.txt", "w") as file:
            for line in report_lines:
                file.write(line + "\n")

    @staticmethod
    def get_days_difference(first_date: datetime, second_date: datetime) -> int:
        days_difference = abs((first_date - second_date).days)
        if days_difference == 0:
            return first_date.day
        return days_difference

    @staticmethod
    def read_csv(file_path: str) -> list[dict[str, str]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")
        with path.open(newline="") as csvfile:
            return list(csv.DictReader(csvfile))
