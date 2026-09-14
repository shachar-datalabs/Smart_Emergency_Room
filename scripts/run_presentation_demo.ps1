[CmdletBinding()]
param(
    [string]$ProjectId = "shachar-bigquery-lab",
    [string]$Dataset = "smart_er_gold",
    [string]$LookerStudioUrl = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ===" -ForegroundColor Cyan
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

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is required."
}
if (-not (Get-Command bq -ErrorAction SilentlyContinue)) {
    throw "The Google Cloud CLI with bq is required."
}
docker version | Out-Null

$env:GCP_PROJECT = $ProjectId
$env:BIGQUERY_GOLD_DATASET = $Dataset
$env:GCP_REGION = "us-central1"

Write-Step "Running the end-to-end proof"
Write-Host "The script will show:"
Write-Host "1. Active patients before the new event"
Write-Host "2. One ARRIVAL event through Kafka and Spark"
Write-Host "3. BigQuery synchronization"
Write-Host "4. Active patients after the new event"
Invoke-Python scripts/demo_bigquery.py

Write-Step "Showing BigQuery Gold tables"
bq head --max_rows=10 "${ProjectId}:${Dataset}.ed_kpis"
bq head --max_rows=10 "${ProjectId}:${Dataset}.active_patients"

Write-Step "Opening the dashboard"
$DashboardPath = Join-Path $ProjectRoot "dashboards\smart_er_dashboard.html"
if (Test-Path $DashboardPath) {
    Start-Process $DashboardPath
}
if ($LookerStudioUrl) {
    Start-Process $LookerStudioUrl
}

Write-Host ""
Write-Host "LIVE DEMO PASSED" -ForegroundColor Green
Write-Host "Look for status PASS and verify that after equals before plus one."
