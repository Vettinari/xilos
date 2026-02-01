.PHONY: install install-all test lint format clean build build-serve up down train serve install-python

# Configuration
PYTHON_VERSION := 3.11.9
VENV := .venv
PYTHON := $(VENV)/bin/python
POETRY := $(VENV)/bin/poetry

# Install Python and Setup Venv with Poetry
install-python:
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
	$(POETRY) install --with train,serve,aws,azure,gcp
	$(POETRY) run pre-commit install

test:
	$(POETRY) run pytest tests/ -v --cov=src/xilos

lint:
	$(POETRY) run ruff check .
	$(POETRY) run ruff format --check .

format:
	$(POETRY) run ruff check --fix .
	$(POETRY) run ruff format .

clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ dist build coverage.xml .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +

clean-venv:
	rm -rf $(VENV)

# Docker commands
# Default build uses Alpine
build:
	docker build -t xilos:latest .

# Build with Bookworm
build-bookworm:
	docker build -f bookworm.Dockerfile -t xilos:bookworm .

up:
	docker-compose up -d

down:
	docker-compose down

# Helper aliases
train:
	$(POETRY) run python -m xilos.xtrain.main

serve:
	$(POETRY) run python -m xilos.xserve.main
