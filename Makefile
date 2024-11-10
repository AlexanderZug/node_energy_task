#
# environment
#
.DEFAULT_GOAL := help
SHELL := /bin/bash
APPNAME := create-invioce
CONTAINER_IMAGE_NAME := ${APPNAME}
PYTHON_VERSION := 3.12
PYTHON_VENV := ${APPNAME}

#
# includes
#
include makefiles/*

#
# help
#
help: main_help help_python help_git
main_help:
	@echo ""
	@echo "make clean -------------------- Delete temporary/cache files etc."
	@echo "make run-test ----------------- Run the test"
	@echo "make setup -------------------- Set up VENV and git-hooks"
	@echo ""

clean:
	@echo "executing target clean"
	@rm -rf \
		.coverage \
		.mypy_cache/ \
		.ruff_cache/ \
		.pytest_cache/ \
		cov/
	@find . -type d -name "__pycache__" -prune -exec rm -rf "{}" \;

#
# run targets
#
run-test:
	@echo "executing target run-test"
	@pytest src/tests/

setup: venv-setup git-install-hooks
