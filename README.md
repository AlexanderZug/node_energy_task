# Energy Delivery Cost Calculation Script

The script calculates the cost of energy delivery and generates an invoice report.
The project can be set up and run using simple commands.

## Setup

To set up the project, run the following command:

```
make setup
```

This command activates the virtual environment (using `pyenv`) and
installs all required dependencies using the `poetry` package manager.

## Usage

To run the script and create an invoice, use the `create_invoice` command
with the required parameters. You need to specify the `customer ID`, `year`,
and `month` for which the report should be generated. There are also two optional parameters:
`--customer-file` (path to the customer data file) and `--values-file` (path to the electricity consumption data file).
By default, these parameters are set to `data/customers.csv` and `data/meter_values.csv`.

Example Command

```
create_invoice --id 533ec7 -y 2021 -m 6
```

After running this command, the script generates a .txt report file and
places it in the reports directory at the root of the project.

## Tests

To run the test suite, use the following command:

```
make run-test
```
