@echo off
REM Change directory to the location of this batch file
cd /d "%~dp0"

REM Check if the virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [SETUP] No virtual environment found. Creating one now...
    python -m venv venv
    
    echo [SETUP] Installing required packages...
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install pandas openpyxl reportlab
) else (
    echo [INFO] Activating existing virtual environment...
    call venv\Scripts\activate.bat
)

echo [RUN] Starting label generator...
python Generate_Labels.py

REM Keep the terminal window open to view the results
pause
