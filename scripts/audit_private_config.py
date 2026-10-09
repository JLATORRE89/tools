"""Report filenames containing known private settings, never the values."""
from pathlib import Path
import os, subprocess, sys
from repo_env import load_env, ROOT

def main():
    load_env()
    keys = ['LOCALNET_HOST','OPENCLAW_HOST','LOCALNET_SSH_TARGET','OPENCLAW_SSH_TARGET',
            'SERVICE_USER_HOME','TELEGRAM_DM_ID','TELEGRAM_BOT_USERNAME',
            'TELEGRAM_WEBUI_CHANNEL_ID','DNS_OPERATOR_CHECKOUT']
    values = [os.environ[k] for k in keys if os.environ.get(k)]
    if not values:
        print('Audit cannot run without private configuration; see CONFIGURATION.md.')
        return 1
    names = subprocess.check_output(['git','ls-files','-co','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    bad = set()
    for name in names:
        path = ROOT / name
        if path.name == '.env' or (path.name.startswith('.env.') and not path.name.endswith('.example')):
            bad.add(name);continue
        if not path.is_file() or path.stat().st_size > 2_000_000:continue
        try: text = path.read_text(encoding='utf-8-sig')
        except (UnicodeError,OSError):continue
        if any(value in text for value in values):bad.add(name)
    if bad:
        print('Private configuration appears in publishable files:\n'+'\n'.join(sorted(bad)))
        return 1
    print('Private configuration audit passed; .env values were not printed.')
    return 0
if __name__ == '__main__':sys.exit(main())
