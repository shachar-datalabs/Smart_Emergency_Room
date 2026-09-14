[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command was not found: $Name"
    }
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    $script:PythonExe = "py"
    $script:PythonPrefix = @("-3")
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $script:PythonExe = "python"
    $script:PythonPrefix = @()
}
else {
    throw "Python 3.11 or newer is required."
}

function Invoke-Python {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    $allArguments = $script:PythonPrefix + $Arguments
    & $script:PythonExe @allArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

Write-Step "Checking prerequisites"
Require-Command git
Require-Command docker
Require-Command bq
Invoke-Python --version
docker version | Out-Null
docker compose version
bq version

if (-not (Test-Path ".env")) {
    Write-Step "Creating local .env"
    Copy-Item ".env.example" ".env"
}

if (-not $SkipInstall) {
    Write-Step "Installing Python dependencies"
    Invoke-Python -m pip install -r requirements.txt
}

if (-not (Test-Path "data/raw/nhamcs/2022")) {
    Write-Step "Downloading the CDC NHAMCS 2022 source"
    Invoke-Python scripts/download_data.py
}

if (-not (Test-Path "data/gold/current_ed_state_base.jsonl")) {
    Write-Step "Building historical and deterministic demo outputs"
    Invoke-Python scripts/run_historical_pipeline.py
    Invoke-Python scripts/run_end_to_end_demo.py
}

Write-Step "Validating Docker configuration"
docker compose config --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose validation failed."
}

Write-Step "Checking Kafka and Spark containers"
docker compose up -d
try {
    docker compose ps
}
finally {
    docker compose down
}

Write-Step "Checking the BigQuery load plan without writing"
Invoke-Python scripts/sync_bigquery.py

if ($RunTests) {
    Write-Step "Running project tests"
    Invoke-Python -m unittest discover -s tests -v
    Invoke-Python -m unittest discover -s batch/tests -p "test*.py" -v
    Invoke-Python scripts/test_phase0.py
}

Write-Host ""
Write-Host "PREPARATION PASSED" -ForegroundColor Green
Write-Host "Run the live demo with:"
Write-Host ".\scripts\run_presentation_demo.ps1"
