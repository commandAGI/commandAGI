#!/usr/bin/env pwsh
# Script to delete and rebuild API documentation files

Write-Host "Starting API documentation rebuild process..." -ForegroundColor Cyan

# Step 1: Delete existing API documentation directories
Write-Host "Deleting existing API documentation files..." -ForegroundColor Yellow

$apiDirs = @(
    "docs/api/core",
    "docs/api/computers", 
    "docs/api/provisioners",
    "docs/api/daemon",
    "docs/api/gym",
    "docs/api/processors"
)

foreach ($dir in $apiDirs) {
    if (Test-Path $dir) {
        Write-Host "  Removing $dir..." -ForegroundColor Gray
        Remove-Item -Path $dir -Recurse -Force
    }
}

# Step 2: Recreate the directories
Write-Host "Recreating API documentation directories..." -ForegroundColor Yellow
foreach ($dir in $apiDirs) {
    if (-not (Test-Path $dir)) {
        Write-Host "  Creating $dir..." -ForegroundColor Gray
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}

# Step 3: Run the API documentation generator
Write-Host "Rebuilding API documentation..." -ForegroundColor Yellow
try {
    python docs/generate_api_docs.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "API documentation successfully rebuilt!" -ForegroundColor Green
    } else {
        Write-Host "Error: API documentation generation failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error: Failed to run API documentation generator: $_" -ForegroundColor Red
    exit 1
}

Write-Host "API documentation rebuild process complete!" -ForegroundColor Cyan 