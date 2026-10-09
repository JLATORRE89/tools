#!/usr/bin/env python3
"""Install the adjacent assistant for the current Linux desktop user."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime

home = Path.home()
source = Path(__file__).resolve().parent
app = home / '.local/share/monopoly-assist'
bin_dir = home / 'bin'
unit_dir = home / '.config/systemd/user'
desktop = Path(subprocess.check_output(['xdg-user-dir', 'DESKTOP'], text=True).strip())
applications = home / '.local/share/applications'
backup = home / '.local/state/monopoly-assist/backups' / datetime.now().strftime('%Y%m%d-%H%M%S')

def write(path, text, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        saved = backup / path.relative_to(home)
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, saved)
    path.write_text(text, encoding='utf-8', newline='\n')
    path.chmod(0o755 if executable else 0o644)

original = (source / 'monopoly-go-assist').read_text(encoding='utf-8')
old = 'ADB = "/ai/android-sdk/platform-tools/adb"'
assert original.count(old) == 1, 'Unexpected upstream ADB configuration'
write(app / 'monopoly-go-assist', original.replace(old, 'ADB = "/usr/bin/adb"'), True)
for name in ('test_monopoly_go_assist.py', 'RULES.md'):
    write(app / name, (source / name).read_text(encoding='utf-8'))
shutil.copytree(source / 'fixtures', app / 'fixtures', dirs_exist_ok=True)

# Run the existing suite against the actual ARM installation before adding launchers.
result = subprocess.run([sys.executable, '-m', 'unittest', 'test_monopoly_go_assist', '-q'],
                        cwd=app, capture_output=True, text=True)
write(app / 'installation-tests.log', result.stdout + result.stderr)
if result.returncode:
    print(result.stderr[-5000:])
    raise SystemExit(result.returncode)
print(result.stderr[-250:])
(home / '.local/state/monopoly-assist').mkdir(parents=True, exist_ok=True)

write(unit_dir / 'monopoly-assist.service', '''[Unit]
Description=Monopoly GO Assistant
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.local/share/monopoly-assist/monopoly-go-assist loop
Environment=PYTHONUNBUFFERED=1
Environment=OMP_THREAD_LIMIT=1
Environment=MONOPOLY_INPROCESS_OCR=1
Environment=MONOPOLY_METRICS=1
Environment=MONOPOLY_DIAGNOSTICS=1
StandardOutput=append:%h/.local/state/monopoly-assist/assistant.log
StandardError=inherit
Restart=on-failure
RestartSec=10
RestartPreventExitStatus=75
KillSignal=SIGINT
TimeoutStopSec=15
''')

write(bin_dir / 'monopoly', '''#!/usr/bin/env bash
set -euo pipefail
service=monopoly-assist.service
log="$HOME/.local/state/monopoly-assist/assistant.log"
start_assistant() {
    systemctl --user start "$service"
    sleep 1
    if ! systemctl --user is-active --quiet "$service"; then
        tail -n 12 "$log" 2>/dev/null || true
        return 1
    fi
    echo "Monopoly Assist is running in the background."
    echo "Connect the phone by USB, approve USB debugging, and open Monopoly GO."
    echo "Commands: monopoly stop | monopoly status | monopoly logs"
    /usr/bin/adb devices
}
case "${1:-start}" in
    start) start_assistant ;;
    stop) systemctl --user stop "$service"; echo "Monopoly Assist stopped." ;;
    status)
        systemctl --user --no-pager status "$service" || true
        tail -n 8 "$log" 2>/dev/null || true
        /usr/bin/adb devices
        ;;
    logs) touch "$log"; tail -n 40 -F "$log" ;;
    desktop)
        start_assistant || echo "Startup failed. See the details above."
        echo
        read -r -p "Press Enter to close this window. The assistant stays running." || true
        ;;
    *) echo "Usage: monopoly [start|stop|status|logs]"; exit 2 ;;
esac
''', True)

entry = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Monopoly Assist
Comment=Start Monopoly GO automation for your USB-connected Android phone
Exec={bin_dir}/monopoly desktop
Icon=applications-games
Terminal=true
Categories=Game;
StartupNotify=false
Actions=Stop;Status;

[Desktop Action Stop]
Name=Stop Monopoly Assist
Exec={bin_dir}/monopoly stop

[Desktop Action Status]
Name=Monopoly Assist Status
Exec=lxterminal -e bash -c "{bin_dir}/monopoly status; read -p 'Press Enter to close'"
'''
write(desktop / 'monopoly-assist.desktop', entry, True)
write(applications / 'monopoly-assist.desktop', entry)

aliases = home / '.bash_aliases'
existing = aliases.read_text() if aliases.exists() else ''
alias_line = 'alias monopoly="$HOME/bin/monopoly"'
if alias_line not in existing.splitlines():
    write(aliases, existing.rstrip() + '\n\n# Monopoly GO Assistant\n' + alias_line + '\n')

write(app / 'README.txt', '''Monopoly Assist

Double-click Monopoly Assist on the desktop, or run: monopoly
Stop: monopoly stop
Status: monopoly status
Follow logs: monopoly logs (Ctrl+C closes logs without stopping the assistant)

The assistant runs in the background until stopped or the Pi shuts down.
It does not automatically start at boot. Repeated launches reuse one service.
In an already-open terminal, run: source ~/.bash_aliases

Connect the same calibrated Android phone by USB. Enable USB debugging,
approve this Pi on the phone, unlock it and open Monopoly GO.
The screen calibration expects 1080x2340. Other phones need recalibration.
Disconnected or unfocused game sessions wait without blind taps.

Installation tests: ~/.local/share/monopoly-assist/installation-tests.log
Runtime log: ~/.local/state/monopoly-assist/assistant.log
''')
subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
subprocess.run(['desktop-file-validate', str(desktop / 'monopoly-assist.desktop')], check=True)
subprocess.run(['bash', '-n', str(bin_dir / 'monopoly')], check=True)
print('Installed:', desktop / 'monopoly-assist.desktop')
print('Assistant SHA256:', hashlib.sha256((app / 'monopoly-go-assist').read_bytes()).hexdigest())
