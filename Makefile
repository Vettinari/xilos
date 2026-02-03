# Configuration
PYTHON_VERSION := 3.11.9
POETRY_VERSION := 2.3.2

VENV := .venv
PYTHON := $(VENV)/bin/python
POETRY := $(VENV)/bin/poetry


compile:
	@echo "Compiling pyproject.toml..."
	PYTHONPATH=src python3 -m xilos.compile_project

# Install Python and Setup Venv with Poetry
install-python: compile
	@echo "Ensuring Python $(PYTHON_VERSION) is available..."
	@set -e; \
	PYBIN=python$(PYTHON_VERSION); \
	if command -v pyenv >/dev/null 2>&1; then \
		pyenv install $(PYTHON_VERSION) -s; \
		pyenv local $(PYTHON_VERSION); \
	else \
		echo "pyenv not found, using system python $(PYTHON_VERSION) if available..."; \
		if ! command -v $$PYBIN >/dev/null 2>&1; then \
			if python3 --version 2>&1 | grep -q "Python $(PYTHON_VERSION)"; then \
				PYBIN=python3; \
			else \
				echo "Python $(PYTHON_VERSION) is not installed. Please install it or use pyenv"; \
				exit 1; \
			fi; \
		fi; \
	fi; \
	echo "Creating virtual environment..."; \
	if [ ! -d "$(VENV)" ]; then \
		$$PYBIN -m venv $(VENV); \
	fi; \
	echo "Installing Poetry in virtual environment..."; \
	$(VENV)/bin/pip install -U pip setuptools poetry

install: install-python
	@echo "Installing dependencies..."
	$(POETRY) install
	$(POETRY) run pre-commit install

install-all: install-python
	@echo "Installing all dependencies..."
	$(POETRY) install --with serve,aws,azure,gcp,dev
	$(POETRY) run pre-commit install

build:
	@echo "Running project generator..."
	PYTHONPATH=src $(POETRY) run python -m xilos.main

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf .venv  || true
	@rm -rf pyproject.toml || true
	@rm -rf poetry.lock || true
	@echo "Cleaned."

inspect:
	@echo "Running pre-commit checks..."
	$(POETRY) run pre-commit run --all-files
