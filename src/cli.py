import logging
from argparse import ArgumentParser, Namespace

from src.invoice import Invoice

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_cli_options() -> Namespace:
    parser = ArgumentParser(
        description="Generator of invoice files for the given year and month"
    )
    parser.add_argument(
        "--id",
        type=str,
        required=True,
        help="Customer ID",
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        required=True,
        help="Year",
    )
    parser.add_argument(
        "-m",
        "--month",
        type=int,
        required=True,
        help="Month",
    )
    parser.add_argument(
        "--customer-file",
        type=str,
        required=True,
        help="Customer file",
    )
    parser.add_argument(
        "--values-file",
        type=str,
        required=True,
        help="Meter values file",
    )
    return parser.parse_args()


def create_invoice() -> None:
    options: Namespace = get_cli_options()
    invoice: Invoice = Invoice(
        options.id,
        options.year,
        options.month,
        options.customer_file,
        options.values_file,
    )

    try:
        invoice.make_report()
        logger.info("Invoice created successfully")
    except Exception as exc:
        logger.error("An error occurred: %s", exc)


def main() -> None:
    create_invoice()


if __name__ == "__main__":
    main()
