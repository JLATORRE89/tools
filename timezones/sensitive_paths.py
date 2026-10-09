"""Block sensitive filesystem-like URL paths before route/static dispatch."""
from urllib.parse import unquote

SUFFIXES = ('.env','.db','.sqlite','.sqlite3','.sql','.log','.tar','.gz','.zip','.7z',
            '.tgz','.bak','.backup','.pem','.key','.p12','.pfx','~')

def is_sensitive_public_path(path):
    for _ in range(4):
        decoded = unquote(path)
        if decoded == path: break
        path = decoded
    parts = path.replace('\\','/').lower().split('/')
    for part in parts:
        if (part.startswith('.') or part in {'logs','backup','backups','credentials.json','token.json','id_rsa','id_ed25519'}
                or part.endswith(SUFFIXES) or '\x00' in part):
            return True
    return False
