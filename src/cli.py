import logging
from argparse import ArgumentParser, Namespace

from src.invoice import Invoice

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s"
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
    return parser.parse_args()


def create_invoice() -> None:
    options: Namespace = get_cli_options()
    invoice: Invoice = Invoice(
        options.id,
        options.year,
        options.month,
    )
    invoice.make_report()
    # messages: CheckMessages = CheckMessages()
    #
    # try:
    #     status: str = proxy_check.get_state()
    # except Exception as exc:
    #     logger.exception(exc)
    #     messages.unknown(f"Error: {exc!r}")
    #     return exit_check(messages)
    #
    # message_text = f"Interface status: {status}"
    # if status == "Secured":
    #     messages.ok(message_text)
    # elif status == "Unsecured":
    #     messages.critical(message_text)
    # else:
    #     messages.warning(message_text)
    # return exit_check(messages)


def main() -> None:
    create_invoice()


if __name__ == "__main__":
    main()
