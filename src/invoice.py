import calendar
import csv
from datetime import datetime, timedelta
from decimal import ROUND_UP, Decimal
from pathlib import Path

from dateutil import parser


class Invoice:
    def __init__(
        self,
        customer_id: str,
        year: int,
        month: int,
        customers_file: str | Path,
        values_file: str | Path,
    ) -> None:
        self.customer_id = customer_id
        self.year = year
        self.month = month
        self.customers_file = customers_file
        self.values_file = values_file

    def get_customer(self) -> list[dict[str, str]]:
        customers = self.read_csv(self.customers_file)
        return [
            customer for customer in customers if customer["id"] == self.customer_id
        ]

    def get_meter_values(self) -> list[dict[str, str]]:
        meter_values = self.read_csv(self.values_file)
        return [
            row
            for row in meter_values
            if row["customer"] == self.customer_id
            and parser.parse(row["date"]).year == self.year
        ]

    def check_customer_exists(self) -> None:
        if not self.get_customer():
            raise ValueError(f"Customer with id {self.customer_id} not found.")

    def check_values_exist(self) -> None:
        if not self.get_meter_values():
            raise ValueError(f"Date with year {self.year} not found.")

    def get_sorted_values(self) -> list[str]:
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
        if first_date.month < self.month:
            return sorted_dates
        raise ValueError

    def check_sufficient_data_available_in_the_future(
        self, sorted_dates: list[str]
    ) -> list[str]:
        last_date = parser.parse(sorted_dates[-1])
        if last_date.month > self.month:
            return sorted_dates
        raise ValueError

    def get_base_price(self) -> Decimal:
        base_tariff = Decimal(self.get_customer()[0]["base_tariff"])
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        base_price = base_tariff / Decimal(self.days_in_year()) * Decimal(days_in_month)
        return base_price.quantize(Decimal("0.01"), rounding=ROUND_UP)

    def get_energy_price(self) -> Decimal:
        energy_tariff = Decimal(self.get_customer()[0]["energy_tariff"])
        consumptions = self.get_interval_consumption()

        share_period = [
            date
            for date in self.insert_missing_month(consumptions)
            if parser.parse(str(date["date"])).month == self.month
        ]

        energy_price = Decimal(share_period[-1]["value"]) * (
            energy_tariff / Decimal(100)
        )
        return energy_price.quantize(Decimal("0.01"), rounding=ROUND_UP)

    def insert_missing_month(
        self, consumptions: list[dict[str, str | Decimal]]
    ) -> list[dict[str, Decimal | str]]:
        meter_values = self.get_meter_values()

        if len(consumptions) == 1:
            last_record = meter_values[-1]
            add_last_record: dict[str, str | Decimal] = {
                "date": last_record["date"],
                "value": Decimal(last_record["value"]),
            }
            consumptions.append(add_last_record)

        for index in range(len(consumptions) - 1):
            current_date = parser.parse(str(consumptions[index]["date"]))
            next_date = parser.parse(str(consumptions[index + 1]["date"]))

            if current_date.month < self.month < next_date.month:
                new_date = datetime(self.year, self.month, 1)
                next_value_dict = next(
                    (
                        value
                        for value in meter_values
                        if parser.parse(value["date"]) == next_date
                    ),
                )

                new_entry: dict[str, str | Decimal] = {
                    "date": new_date.strftime("%Y-%m-%d"),
                    "value": Decimal(
                        calendar.monthrange(self.year, self.month)[1]
                        / self.get_days_difference(current_date, next_date)
                        * float(next_value_dict["value"])
                    ),
                }

                consumptions.append(new_entry)
                break
        return consumptions

    def get_interval_consumption(self) -> list[dict[str, Decimal | str]]:
        dates = self.check_sufficient_data_available(self.get_sorted_values())
        meter_values = self.get_meter_values()
        share_period: list[dict[str, Decimal | str]] = []

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
                    ).quantize(Decimal("1"), rounding=ROUND_UP),
                }
            )
        return share_period

    def days_in_year(self) -> int:
        return 366 if calendar.isleap(self.year) else 365

    def get_month_range(self) -> str:
        first_day = datetime(self.year, self.month, 1)

        last_day_number = calendar.monthrange(self.year, self.month)[1]
        last_day = datetime(self.year, self.month, last_day_number)

        return f"{first_day.strftime('%d.%m.%Y')} bis {last_day.strftime('%d.%m.%Y')}"

    def make_report(self, dir_name: str | Path = "reports") -> None:
        self.check_customer_exists()
        self.check_values_exist()

        energy_price = self.get_energy_price()
        base_price = self.get_base_price()

        customer_info = self.get_customer()[0]
        customer_name = customer_info["name"]
        customer_street = customer_info["street"]
        customer_postcode = customer_info["postcode"]
        customer_city = customer_info["city"]
        period = self.get_month_range()
        days_in_month = calendar.monthrange(self.year, self.month)[1]
        base_tariff = Decimal(customer_info["base_tariff"])
        energy_tariff = Decimal(customer_info["energy_tariff"])
        share_period_value = energy_price / (energy_tariff / Decimal(100))
        total_price = base_price + energy_price

        report_lines = [
            f"{customer_name}",
            f"{customer_street}",
            f"{customer_postcode} {customer_city}",
            f"Abrechnungszeitraum {period}",
            "Komponente    Anzahl    Preis        Kosten",
            "----------------------------------------------",
            f"Grundpreis    {days_in_month} Tage x {base_tariff} €/Jahr = {base_price:.2f} €",
            f"Arbeitspreis  {share_period_value.quantize(Decimal('1'), rounding=ROUND_UP)} kWh x "
            f"{energy_tariff} ct/kWh = {energy_price:.2f} €",
            "----------------------------------------------",
            f"Summe        {total_price:.2f} €",
        ]

        file_path = Path(f"{dir_name}/report_{customer_info['id']}_{self.month}.txt")
        with file_path.open("w") as file:
            for line in report_lines:
                file.write(line + "\n")

    @staticmethod
    def get_days_difference(first_date: datetime, second_date: datetime) -> int:
        return abs((first_date - second_date).days)

    @staticmethod
    def read_csv(file_path: str | Path) -> list[dict[str, str]]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")
        with path.open(newline="") as csvfile:
            return list(csv.DictReader(csvfile))
