param (
    [Parameter(Mandatory=$false)]
    [string]$Command = "help"
)

# Ensure .venv is used if present
$VenvBin = Join-Path $PSScriptRoot ".venv\Scripts"
if (Test-Path $VenvBin) {
    $env:PATH = "$VenvBin;$env:PATH"
}

switch ($Command) {
    "install" {
        Write-Host "Installing package with dev dependencies..." -ForegroundColor Cyan
        pip install -e .[dev]
    }
    "test" {
        Write-Host "Running tests..." -ForegroundColor Cyan
        pytest
    }
    "lint" {
        Write-Host "Running linting and type checks..." -ForegroundColor Cyan
        ruff check .
        mypy src tests
    }
    "format" {
        Write-Host "Formatting code..." -ForegroundColor Cyan
        ruff format .
    }
    "run" {
        Write-Host "Starting FastAPI dev server..." -ForegroundColor Cyan
        uvicorn financial_platform.api.main:app --reload --host 127.0.0.1 --port 8000
    }
    "clean" {
        Write-Host "Cleaning build and cache artifacts..." -ForegroundColor Cyan
        Get-ChildItem -Path . -Recurse -Include "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    }
    Default {
        Write-Host "Available commands (PowerShell):" -ForegroundColor Yellow
        Write-Host "  .\tasks.ps1 install  - Install package with development dependencies"
        Write-Host "  .\tasks.ps1 test     - Run pytest test suite"
        Write-Host "  .\tasks.ps1 lint     - Run ruff check and mypy type checks"
        Write-Host "  .\tasks.ps1 format   - Run ruff code formatter"
        Write-Host "  .\tasks.ps1 run      - Start FastAPI development server"
        Write-Host "  .\tasks.ps1 clean    - Remove build and cache artifacts"
    }
}
