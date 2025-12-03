# Build Script for SAP Price Updater
# This script uses PyInstaller to create a standalone executable with a clean venv.

Write-Host "=== SAP Price Updater Build Script ===" -ForegroundColor Cyan

# Venv folder name
$venvPath = ".\venv_build"

# Step 1: Remove existing venv if it exists
Write-Host "`n[1/4] Checking for existing virtual environment..." -ForegroundColor Yellow
if (Test-Path $venvPath) {
    Write-Host "      Removing existing venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
}

# Step 2: Create new clean venv
Write-Host "`n[2/4] Creating new virtual environment..." -ForegroundColor Yellow
python -m venv $venvPath

# Step 3: Install dependencies
Write-Host "`n[3/4] Installing required packages..." -ForegroundColor Yellow
& "$venvPath\Scripts\pip.exe" install pandas openpyxl pyinstaller

# Step 4: Build the executable
Write-Host "`n[4/4] Building executable with PyInstaller..." -ForegroundColor Yellow
& "$venvPath\Scripts\pyinstaller.exe" --noconfirm --onedir --windowed --clean --name "SapPriceUpdater" "src\main.py"

Write-Host "`n=== Build Complete ===" -ForegroundColor Green
Write-Host "Executable located at: dist\SapPriceUpdater\SapPriceUpdater.exe" -ForegroundColor Green