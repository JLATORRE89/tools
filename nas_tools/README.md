# nas_tools

Western Digital (WD) My Cloud discovery and SMB mounting utilities.

- **Author:** Jason LaTorre  
- **Version:** 1.0.0  
- **License:** 

## Highlights
- SSDP/UPnP discovery with `python -m nas_tools.wd_discovery` or `wd-discovery`.
- Cross-platform SMB mounting with `python -m nas_tools.wd_mount` or `wd-mount`.
- Automatic UTF-8 logging (`wd_discovery.log`, `wd_mount.log`) stored next to the package.
- Auto-provisioned `config.xml` with Base64 passwords and shared between both tools.
- Console options `--status`, `--setup`, `--debug`, `--umount` for automation and diagnostics.

## Installation

```bash
pip install -e .
```

Or build a wheel:

```bash
python setup.py sdist bdist_wheel
pip install dist/nas_tools-1.0.0-py3-none-any.whl
```

## CLI Usage

| Task            | Command                                      |
|-----------------|----------------------------------------------|
| Discover NAS    | `python -m nas_tools.wd_discovery`           |
| Discovery setup | `python -m nas_tools.wd_discovery --setup`   |
| Mount share     | `python -m nas_tools.wd_mount`               |
| Mount setup     | `python -m nas_tools.wd_mount --setup`       |
| Unmount share   | `python -m nas_tools.wd_mount --umount`      |
| Script-friendly | `python -m nas_tools.wd_mount --status`      |

The console scripts `wd-discovery` and `wd-mount` expose the same behavior once the package is installed.

## Configuration (config.xml)

`config.xml` is generated automatically on first run and lives in `nas_tools/config.xml`.

```xml
<?xml version="1.0" encoding="utf-8"?>
<config>
  <network>
    <timeout>5</timeout>
  </network>
  <share>
    <hostname>MYCLOUD</hostname>
    <ip></ip>
    <smb_share>Public</smb_share>
    <username>guest</username>
    <password encoding="base64">bXlwYXNzd29yZA==</password>
    <mount_point>/mnt/mycloud</mount_point>
    <drive_letter>Z:</drive_letter>
  </share>
</config>
```

- Edit the file on Windows, macOS, or Linux—the scripts use UTF-8 and handle CRLF/LF transparently.
- Base64 passwords can be produced with `python -c "import base64; print(base64.b64encode(b'MyPassword').decode())"`.

## Quick Integration Guide

1. **Install in your environment** with `pip install -e .` (or regular `pip install nas_tools` when published).  
   This exposes both `nas_tools` modules and the console scripts.
2. **Ensure `config.xml` exists** at process startup:
   ```python
   from nas_tools import wd_discovery
   wd_discovery.ensure_default_config()
   ```
3. **Let your UI or API update credentials** by loading the dict, adjusting keys, and writing it back. Passwords can stay in plain text—the helper re-encodes them to Base64.
4. **Call discovery/mount helpers** from background jobs or request handlers as needed.

```python
from nas_tools import wd_discovery, wd_mount

# Provision once
wd_discovery.ensure_default_config()

# Example: save user-supplied creds from a web form
cfg = wd_discovery.load_config()
cfg.update(
    hostname=form["hostname"],
    ip=form.get("ip", ""),
    smb_share=form.get("share", "Public"),
    username=form["username"],
    password=form["password"],
    mount_point=form.get("mount_point", "/mnt/mycloud"),
    drive_letter=form.get("drive_letter", "Z:")
)
wd_discovery._write_config(cfg)  # trusted backend call

# Later: discover and mount
devices = wd_discovery.find_nas(verbose=False)
if devices:
    logger = wd_mount._build_logger()
    wd_mount.mount_share({**cfg, "ip": devices[0]["ip"]}, devices[0]["ip"], logger)
else:
    print("No WD My Cloud devices found")
```

Because the XML format is portable, you can edit it on Windows 11, move it to macOS or Ubuntu/RHEL 9, and the modules will continue to parse it without any extra conversion steps (no `dos2unix` required).

## Logging

| Module        | Log file              |
|---------------|-----------------------|
| wd_discovery  | `nas_tools/wd_discovery.log` |
| wd_mount      | `nas_tools/wd_mount.log`      |

Logs are timestamped, UTF-8 encoded, and rolled manually by the user (delete or rotate as needed).

## Automation Example

```bash
# Check mount status every hour on Linux
0 * * * * /usr/bin/python3 -m nas_tools.wd_mount --status >> /var/log/wd_mount.log 2>&1
```

## Version History

| Version | Date       | Notes                                                   |
|---------|------------|---------------------------------------------------------|
| 1.0.0   | Nov 2025   | Initial release with discovery + mount modules.         |

