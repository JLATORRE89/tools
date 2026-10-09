"""Load this checkout's ignored .env without executing shell code."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_env(path=None):
    path = Path(path or os.environ.get('TOOLS_ENV_FILE', ROOT / '.env'))
    if not path.is_file():
        return path
    for number, line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'): continue
        key, sep, value = line.partition('=')
        key = key.strip(); value = value.strip()
        if not sep or not key.replace('_', '').isalnum() or key[0].isdigit():
            raise ValueError(f'Invalid env key on line {number}')
        if value.startswith('"'): value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"): value = value[1:-1]
        os.environ.setdefault(key, value)
    return path

def require(name):
    load_env()
    value = os.environ.get(name)
    if not value: raise RuntimeError(f'Set {name} in the ignored tools .env; see .env.example and CONFIGURATION.md')
    return value

if __name__ == '__main__':
    p = load_env()
    print('Private environment loaded' if p.is_file() else 'No private environment; see .env.example')
