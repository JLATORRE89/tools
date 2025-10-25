@echo off
REM ============================================================================
REM Proxy Cache Detector - Windows Installation Script
REM ============================================================================
REM This script creates a virtual environment and installs dependencies
REM Compatible with Windows 10, 11, and Server editions
REM ============================================================================

echo.
echo ================================================================================
echo   Proxy Cache Detector - Windows Installation
echo ================================================================================
echo.

REM Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

python --version
echo.

REM Check Python version
echo [2/6] Verifying Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 6) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.6 or higher is required
    echo Please upgrade your Python installation
    echo.
    pause
    exit /b 1
)
echo Python version OK
echo.

REM Check if pip is available
echo [3/6] Checking pip installation...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not installed
    echo.
    echo Please reinstall Python with pip included
    echo.
    pause
    exit /b 1
)

python -m pip --version
echo.

REM Check if virtual environment already exists
echo [4/6] Setting up virtual environment...
if exist venv (
    echo Virtual environment already exists at 'venv'
    echo Skipping creation...
) else (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to create virtual environment
        echo.
        echo Try running this command manually:
        echo   python -m venv venv
        echo.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [5/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to activate virtual environment
    echo.
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Install dependencies
echo [6/6] Installing dependencies in virtual environment...
echo.

if exist requirements.txt (
    echo Installing from requirements.txt...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install dependencies
        echo.
        echo Try running these commands manually:
        echo   venv\Scripts\activate
        echo   python -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
) else (
    echo requirements.txt not found, installing requests directly...
    python -m pip install --upgrade pip
    python -m pip install requests>=2.31.0
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install requests library
        echo.
        echo Try running these commands manually:
        echo   venv\Scripts\activate
        echo   python -m pip install requests
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ================================================================================
echo   Installation Complete!
echo ================================================================================
echo.
echo A virtual environment has been created in the 'venv' directory.
echo.
echo IMPORTANT: To use the tool, you must activate the virtual environment first:
echo.
echo   Activation:
echo     venv\Scripts\activate
echo.
echo   Then run commands:
echo     python proxy_cache_detector.py detect https://example.com
echo     python proxy_cache_detector.py purge-varnish https://example.com/page
echo     python proxy_cache_detector.py --help
echo.
echo   Deactivate when done:
echo     deactivate
echo.
echo For more information, see docs\README.md
echo.
echo The virtual environment is currently ACTIVE for this session.
echo.
pause
