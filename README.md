# Real-Time Financial Data Platform

Distributed financial data engineering platform designed to ingest, process, store, and serve real-time and batch market data.

## Getting Started

### Prerequisites
- Python 3.11+

### Developer Commands

#### On Windows (PowerShell):
- **Install dependencies**: `pip install -e .[dev]` or `.\tasks.ps1 install`
- **Run tests**: `pytest` or `.\tasks.ps1 test`
- **Run linter & type check**: `ruff check .` and `mypy src tests` or `.\tasks.ps1 lint`
- **Format code**: `ruff format .` or `.\tasks.ps1 format`
- **Start development server**: `uvicorn financial_platform.api.main:app --reload` or `.\tasks.ps1 run`
- **Clean build artifacts**: `.\tasks.ps1 clean`

#### On Linux / macOS / CI (Makefile):
- `make install`
- `make test`
- `make lint`
- `make format`
- `make run`
- `make clean`
