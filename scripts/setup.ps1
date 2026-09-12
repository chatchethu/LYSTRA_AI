# Personal AI Agent — Setup Script (Windows PowerShell)
# Run this script to set up the development environment

param(
    [switch]$SkipOllama,
    [switch]$SkipDocker,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Personal AI Agent — Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
function Test-Command {
    param($command)
    try {
        Get-Command $command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-Command "docker")) {
    Write-Host "ERROR: Docker is not installed. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "  https://www.docker.com/products/docker-desktop/" -ForegroundColor Gray
    exit 1
}
Write-Host "  ✓ Docker found" -ForegroundColor Green

if (-not (Test-Command "python")) {
    Write-Host "ERROR: Python 3.12+ is not installed." -ForegroundColor Red
    exit 1
}
$pythonVersion = (python --version 2>&1).ToString()
Write-Host "  ✓ $pythonVersion found" -ForegroundColor Green

if (-not (Test-Command "node")) {
    Write-Host "ERROR: Node.js 20+ is not installed." -ForegroundColor Red
    exit 1
}
$nodeVersion = (node --version).ToString()
Write-Host "  ✓ Node.js $nodeVersion found" -ForegroundColor Green

# Copy .env file
Write-Host ""
Write-Host "Setting up environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ Created .env from .env.example" -ForegroundColor Green
    Write-Host "  ⚠  IMPORTANT: Edit .env and change SECRET_KEY and JWT_SECRET_KEY!" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ .env already exists" -ForegroundColor Green
}

# Create uploads directory
if (-not (Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "  ✓ Created uploads/ directory" -ForegroundColor Green
}

# Pull Ollama models
if (-not $SkipOllama) {
    Write-Host ""
    Write-Host "Pulling Ollama models..." -ForegroundColor Yellow
    Write-Host "  (This may take a while on first run)" -ForegroundColor Gray
    
    if (Test-Command "ollama") {
        $models = @("llama3.2:3b", "nomic-embed-text")
        foreach ($model in $models) {
            Write-Host "  Pulling $model..." -ForegroundColor Gray
            ollama pull $model
            Write-Host "  ✓ $model ready" -ForegroundColor Green
        }
        Write-Host "  Optional models (uncomment to pull):" -ForegroundColor Gray
        Write-Host "    ollama pull qwen2.5-coder:7b  # Better code generation" -ForegroundColor Gray
        Write-Host "    ollama pull llava:7b           # Vision support" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠  Ollama not found. Please install from https://ollama.com" -ForegroundColor Yellow
        Write-Host "     Then run: ollama pull llama3.2:3b && ollama pull nomic-embed-text" -ForegroundColor Gray
    }
}

# Start Docker services
if (-not $SkipDocker) {
    Write-Host ""
    Write-Host "Starting Docker services (PostgreSQL + Redis)..." -ForegroundColor Yellow
    
    docker compose up postgres redis -d
    
    Write-Host "  Waiting for PostgreSQL to be ready..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    Write-Host "  ✓ Docker services started" -ForegroundColor Green
}

# Set up Python backend
Write-Host ""
Write-Host "Setting up Python backend..." -ForegroundColor Yellow

Set-Location "backend"

if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "  ✓ Created Python virtual environment" -ForegroundColor Green
}

# Activate venv and install
& ".\venv\Scripts\Activate.ps1"
pip install -r requirements.txt -q
Write-Host "  ✓ Python dependencies installed" -ForegroundColor Green

# Run migrations
Write-Host "  Running database migrations..." -ForegroundColor Gray
try {
    alembic -c database/alembic.ini upgrade head
    Write-Host "  ✓ Database migrations applied" -ForegroundColor Green
} catch {
    Write-Host "  ⚠  Migration failed. Make sure PostgreSQL is running." -ForegroundColor Yellow
}

Set-Location ".."

# Set up frontend
if (-not $SkipFrontend) {
    Write-Host ""
    Write-Host "Setting up frontend..." -ForegroundColor Yellow
    
    Set-Location "frontend"
    npm install --silent
    Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
    Set-Location ".."
}

# Final instructions
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the development servers:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Terminal 1 — Backend:" -ForegroundColor White
Write-Host "    cd backend" -ForegroundColor Gray
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "    uvicorn backend.main:app --reload --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "  Terminal 2 — Celery Worker:" -ForegroundColor White
Write-Host "    cd backend" -ForegroundColor Gray
Write-Host "    .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "    celery -A backend.workers.celery_app worker --loglevel=info" -ForegroundColor Gray
Write-Host ""
Write-Host "  Terminal 3 — Frontend:" -ForegroundColor White
Write-Host "    cd frontend" -ForegroundColor Gray
Write-Host "    npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "  OR: Start everything with Docker:" -ForegroundColor White
Write-Host "    docker compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "  Open: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
