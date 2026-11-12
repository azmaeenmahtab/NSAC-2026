param(
    [Parameter(Position=0, Mandatory=$false)]
    [ValidateSet("setup", "dev-api", "dev-web", "lint", "lint-py", "lint-web", "test", "test-py", "test-web", "pipeline", "help")]
    [string]$Task = "help"
)

switch ($Task) {
    "setup" {
        Write-Host "Syncing Python packages and installing web dependencies..." -ForegroundColor Cyan
        uv sync --all-packages --all-extras
        pnpm --dir apps/web install
    }
    "dev-api" {
        Write-Host "Starting PyroScope FastAPI Backend on http://localhost:8000..." -ForegroundColor Cyan
        uv run uvicorn app.main:app --app-dir services/api --reload --port 8000
    }
    "dev-web" {
        Write-Host "Starting PyroScope Next.js Web App on http://localhost:3000..." -ForegroundColor Cyan
        pnpm --dir apps/web dev
    }
    "lint" {
        Write-Host "Running Python & Web Linters..." -ForegroundColor Cyan
        uv run ruff check .
        uv run mypy pipeline services/api
        pnpm --dir apps/web typecheck
        pnpm --dir apps/web lint
    }
    "lint-py" {
        uv run ruff check .
        uv run mypy pipeline services/api
    }
    "lint-web" {
        pnpm --dir apps/web typecheck
        pnpm --dir apps/web lint
    }
    "test" {
        Write-Host "Running Python & Web Test Suites..." -ForegroundColor Cyan
        uv run pytest
        pnpm --dir apps/web test
    }
    "test-py" {
        uv run pytest
    }
    "test-web" {
        pnpm --dir apps/web test
    }
    "pipeline" {
        Write-Host "Executing full PyroScope pipeline on raw satellite data..." -ForegroundColor Cyan
        uv run python -m pyroscope_pipeline all
    }
    default {
        Write-Host "PyroScope Windows PowerShell Runner" -ForegroundColor Yellow
        Write-Host "Usage: .\run.ps1 <task>"
        Write-Host "Available tasks:"
        Write-Host "  setup     - Sync uv Python packages and pnpm web packages"
        Write-Host "  dev-api   - Start FastAPI backend (http://localhost:8000)"
        Write-Host "  dev-web   - Start Next.js frontend (http://localhost:3000)"
        Write-Host "  test      - Run full pytest and vitest test suites"
        Write-Host "  lint      - Run ruff, mypy, typescript, and eslint checks"
        Write-Host "  pipeline  - Run data pipeline on raw FIRMS CSVs"
    }
}
