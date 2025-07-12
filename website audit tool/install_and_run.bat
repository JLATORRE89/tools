@echo off
python -m pip install --upgrade pip
pip install -r requirements.txt
echo Launching audit...
python site_audit.py https://visasvista.com
pause
