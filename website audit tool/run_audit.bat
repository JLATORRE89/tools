@echo off
echo == Checking Python ==
python --version || (
    echo [!] Python is not installed. Please install Python 3.7+ from https://www.python.org/downloads/windows/
    pause
    exit /b
)

echo == Installing requirements ==
pip install -r requirements.txt

echo == Starting site audit ==
python site_audit.py https://www.visasvista.com

pause
