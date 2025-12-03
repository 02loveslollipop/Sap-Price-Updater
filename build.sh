#!/bin/bash
# Build Script for SAP Price Updater (Linux/MacOS)
# This script uses PyInstaller to create a standalone executable with a clean venv.

set -e  # Exit on error

echo "=== SAP Price Updater Build Script ==="

# Venv folder name
VENV_PATH="./venv_build"

# Step 1: Remove existing venv if it exists
echo ""
echo "[1/4] Checking for existing virtual environment..."
if [ -d "$VENV_PATH" ]; then
    echo "      Removing existing venv..."
    rm -rf "$VENV_PATH"
fi

# Step 2: Create new clean venv
echo ""
echo "[2/4] Creating new virtual environment..."
python3 -m venv "$VENV_PATH"

# Step 3: Install dependencies
echo ""
echo "[3/4] Installing required packages..."
"$VENV_PATH/bin/pip" install --upgrade pip
"$VENV_PATH/bin/pip" install pandas openpyxl pyinstaller

# Step 4: Build the executable
echo ""
echo "[4/4] Building executable with PyInstaller..."
"$VENV_PATH/bin/pyinstaller" --noconfirm --onedir --windowed --clean --name "SapPriceUpdater" "src/main.py"

echo ""
echo "=== Build Complete ==="
echo "Executable located at: dist/SapPriceUpdater/"
