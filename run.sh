#!/usr/bin/env bash

# Stop immediately if something fails
set -e

# Move into the folder where run.sh is located
cd "$(dirname "$0")"

# If there is no venv yet, create one and install dependencies
if [ ! -d "venv" ]; then
    echo "[SETUP] No virtual environment found. Creating one now..."
    python -m venv venv

    echo "[SETUP] Activating virtual environment..."
    source venv/bin/activate

    echo "[SETUP] Installing required packages..."
    python -m pip install --upgrade pip
    python -m pip install pandas openpyxl reportlab
else
    echo "[INFO] Activating existing virtual environment..."
    source venv/bin/activate
fi

echo "[RUN] Starting label generator..."
python Generate_Labels.py
