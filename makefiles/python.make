#
# help text for this module
#
help_python:
	@echo ""
	@echo "-------------------- Python: Maintenance --------------------------"
	@echo "make requirements ------------- Write dependency lock file"
	@echo "make requirements-up ---------- Upgrade dependencies and create a new commit"
	@echo "make sync --------------------- Sync installed dependencies with lock file"
	@echo ""
	@echo "-------------------- Python: Environment Setup --------------------"
	@echo "make venv-setup --------------- Set up the python VENV for this project"
	@echo "make venv-delete -------------- Delete VENV specified in Makefile"
	@echo "make venv-install ------------- Install VENV with desired python version and sync dependencies"
	@echo "make venv-update -------------- Update basic python tooling like pip, etc,"
	@echo "make venv-reset --------------- Reinstall VENV based on new python-version in Makefile"
	@echo ""
	@echo "-------------------- Python: Tests --------------------------------"
	@echo "make coverage-html ------------ Generate html coverage reports and opens it"
	@echo "make lint --------------------- Run linter"
	@echo "make mypy --------------------- Run mypy tests"
	@echo "make test --------------------- Run all tests"

#
# maintenance targets
#
requirements: venv-update
	@echo "executing target requirements"
	@poetry lock --no-update
	@poetry export --output=requirements.txt

requirements-up: venv-update
	@echo "executing target requirements-up"
	@poetry update
	@poetry export --output=requirements.txt
	@git add \
		poetry.lock \
		requirements.txt
	@git commit -m "Update python dependencies"

sync: venv-update
	@echo "executing target sync"
	@poetry install --sync

#
# setup targets
#
venv-setup: venv-install

venv-delete:
	@echo "executing target venv-delete"
	@pyenv virtualenv-delete -f ${PYTHON_VENV}

venv-install:
	@echo "executing target venv-install"
	@pyenv install -s ${PYTHON_VERSION}
	@pyenv virtualenv -f ${PYTHON_VERSION} ${PYTHON_VENV}
	@test -f .python-version || echo "${PYTHON_VENV}" > .python-version
	@${MAKE} -s venv-update
	@source "$$(pyenv prefix)/bin/activate" \
		&& ${MAKE} -s sync

venv-update:
	@"$$(pyenv prefix)/bin/pip" install -q --upgrade \
		pip \
		setuptools

venv-reset: venv-delete venv-install

#
# test targets
#
coverage-html:
	@echo "executing target coverage"
	@pytest -v \
		--cov-report html:reports/pytest/html \
		--cov-report term \
		--cov=. \
		.
	@xdg-open reports/pytest/html/index.html

lint:
	@echo "executing target lint"
	@ruff check

mypy:
	@echo "executing target mypy"
	@mypy .

.ONESHELL:
test:
	@echo "executing target test"
	FAILED=0
	${MAKE} -s lint || FAILED=1
	${MAKE} -s mypy || FAILED=1
	${MAKE} -s coverage-html || FAILED=1
	exit  $$FAILED
