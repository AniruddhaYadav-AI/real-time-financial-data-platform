.PHONY: help install test lint format run clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install package with development dependencies"
	@echo "  make test     - Run pytest test suite"
	@echo "  make lint     - Run ruff check and mypy type checks"
	@echo "  make format   - Run ruff code formatter"
	@echo "  make run      - Start FastAPI development server"
	@echo "  make clean    - Remove build and cache artifacts"

install:
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check .
	mypy src tests

format:
	ruff format .

run:
	uvicorn financial_platform.api.main:app --reload --host 127.0.0.1 --port 8000

clean:
	python -c "import shutil, glob, os; [shutil.rmtree(p, ignore_errors=True) for p in glob.glob('**/__pycache__', recursive=True) + glob.glob('**/.pytest_cache', recursive=True) + glob.glob('**/.ruff_cache', recursive=True) + glob.glob('**/.mypy_cache', recursive=True) + glob.glob('*.egg-info')]"
