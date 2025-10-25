# Third-Party Licenses

This document contains the licenses and source code locations for all open source software used in VoidGuard Security Enhanced Server Protection.

## Core Security Framework

### Fail2Ban
- **License**: GNU General Public License v2.0 (GPL-2.0)
- **Source Code**: https://github.com/fail2ban/fail2ban
- **Copyright**: © 2004-2023 Cyril Jaquier, Yaroslav Halchenko, and contributors
- **Description**: Intrusion prevention software framework that protects against brute-force attacks

### Python
- **License**: Python Software Foundation License
- **Source Code**: https://github.com/python/cpython
- **Copyright**: © 2001-2023 Python Software Foundation
- **Description**: Python programming language runtime and standard library

## HTTP & Network Libraries

### Requests
- **License**: Apache License 2.0
- **Source Code**: https://github.com/psf/requests
- **Copyright**: © 2019 Kenneth Reitz
- **Description**: HTTP library for Python used for downloading threat intelligence feeds

### urllib3
- **License**: MIT License
- **Source Code**: https://github.com/urllib3/urllib3
- **Copyright**: © 2008-2023 Andrey Petrov and contributors
- **Description**: HTTP client library (dependency of Requests)

### certifi
- **License**: Mozilla Public License 2.0 (MPL-2.0)
- **Source Code**: https://github.com/certifi/python-certifi
- **Copyright**: © 2011-2023 Kenneth Reitz
- **Description**: Python package for providing Mozilla's CA Bundle

## System Integration

### iptables
- **License**: GNU General Public License v2.0 (GPL-2.0)
- **Source Code**: https://git.netfilter.org/iptables/
- **Copyright**: © 1999-2023 Netfilter Core Team
- **Description**: Linux kernel firewall administration tool

### systemd
- **License**: GNU Lesser General Public License v2.1 (LGPL-2.1)
- **Source Code**: https://github.com/systemd/systemd
- **Copyright**: © 2010-2023 systemd contributors
- **Description**: System and service manager for Linux

### cron/cronie
- **License**: MIT License / ISC License
- **Source Code**: https://github.com/cronie-crond/cronie
- **Copyright**: © 1988-2023 Paul Vixie and contributors
- **Description**: Time-based job scheduler in Unix-like operating systems

## Threat Intelligence Sources

### Ipsum Project
- **License**: Creative Commons CC0 1.0 Universal (Public Domain)
- **Source**: https://github.com/stamparm/ipsum
- **Copyright**: © 2017-2023 Miroslav Stampar
- **Description**: Daily updated blacklist of malicious IP addresses

### Spamhaus Project
- **License**: Spamhaus Block List License (Free for non-commercial use)
- **Source**: https://www.spamhaus.org/drop/
- **Copyright**: © 1998-2023 The Spamhaus Project Ltd
- **Description**: Real-time anti-spam protection intelligence

### Tor Project
- **License**: BSD 3-Clause License
- **Source**: https://github.com/torproject/tor
- **Copyright**: © 2001-2023 The Tor Project, Inc.
- **Description**: Tor exit node lists for network anonymity detection

## Configuration & Parsing

### ConfigParser (Python Standard Library)
- **License**: Python Software Foundation License
- **Source Code**: https://github.com/python/cpython/blob/main/Lib/configparser.py
- **Copyright**: © 2001-2023 Python Software Foundation
- **Description**: Configuration file parser for Python

### re (Python Regular Expressions)
- **License**: Python Software Foundation License
- **Source Code**: https://github.com/python/cpython/blob/main/Lib/re.py
- **Copyright**: © 2001-2023 Python Software Foundation
- **Description**: Regular expression operations for pattern matching

## Logging & Monitoring

### rsyslog
- **License**: GNU General Public License v3.0 (GPL-3.0)
- **Source Code**: https://github.com/rsyslog/rsyslog
- **Copyright**: © 2003-2023 Rainer Gerhards and contributors
- **Description**: Rocket-fast system for log processing

### journald (systemd-journald)
- **License**: GNU Lesser General Public License v2.1 (LGPL-2.1)
- **Source Code**: https://github.com/systemd/systemd
- **Copyright**: © 2010-2023 systemd contributors
- **Description**: System service that collects and stores logging data

## Web Server Integration

### Nginx
- **License**: BSD 2-Clause License
- **Source Code**: https://github.com/nginx/nginx
- **Copyright**: © 2002-2023 Igor Sysoev, © 2011-2023 Nginx, Inc.
- **Description**: HTTP and reverse proxy server

### Apache HTTP Server
- **License**: Apache License 2.0
- **Source Code**: https://github.com/apache/httpd
- **Copyright**: © 1999-2023 The Apache Software Foundation
- **Description**: HTTP server software

## Operating System Components

### Linux Kernel
- **License**: GNU General Public License v2.0 (GPL-2.0)
- **Source Code**: https://github.com/torvalds/linux
- **Copyright**: © 1991-2023 Linus Torvalds and contributors
- **Description**: Unix-like operating system kernel

### GNU Core Utilities
- **License**: GNU General Public License v3.0 (GPL-3.0)
- **Source Code**: https://git.savannah.gnu.org/cgit/coreutils.git
- **Copyright**: © 1985-2023 Free Software Foundation, Inc.
- **Description**: Basic file, shell and text manipulation utilities

### Bash
- **License**: GNU General Public License v3.0 (GPL-3.0)
- **Source Code**: https://git.savannah.gnu.org/cgit/bash.git
- **Copyright**: © 1987-2023 Free Software Foundation, Inc.
- **Description**: Bourne Again SHell command interpreter

## Package Management

### APT (Advanced Package Tool)
- **License**: GNU General Public License v2.0 (GPL-2.0)
- **Source Code**: https://github.com/Debian/apt
- **Copyright**: © 1997-2023 Debian Project
- **Description**: Package management system for Debian/Ubuntu

### YUM/DNF
- **License**: GNU General Public License v2.0 (GPL-2.0)
- **Source Code**: https://github.com/rpm-software-management/dnf
- **Copyright**: © 1999-2023 Red Hat, Inc.
- **Description**: Package management system for Red Hat/CentOS/Fedora

## Development & Distribution Tools

### Git
- **License**: GNU General Public License v2.0 (GPL-2.0)
- **Source Code**: https://github.com/git/git
- **Copyright**: © 2005-2023 Linus Torvalds and contributors
- **Description**: Distributed version control system

### curl
- **License**: MIT/X derivate license
- **Source Code**: https://github.com/curl/curl
- **Copyright**: © 1996-2023 Daniel Stenberg and contributors
- **Description**: Command line tool for transferring data with URLs

### wget
- **License**: GNU General Public License v3.0 (GPL-3.0)
- **Source Code**: https://git.savannah.gnu.org/cgit/wget.git
- **Copyright**: © 1995-2023 Free Software Foundation, Inc.
- **Description**: Non-interactive network downloader

---

## License Text References

### GNU General Public License v2.0 (GPL-2.0)
Full text available at: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

### GNU General Public License v3.0 (GPL-3.0)
Full text available at: https://www.gnu.org/licenses/gpl-3.0.html

### MIT License
```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### BSD 2-Clause License
```
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

### Apache License 2.0
Full text available at: https://www.apache.org/licenses/LICENSE-2.0

### Python Software Foundation License
Full text available at: https://docs.python.org/3/license.html

---

## Compliance Notes

1. **GPL Compatibility**: VoidGuard's proprietary components are designed to interact with GPL software through standard interfaces without creating derivative works
2. **Attribution Requirements**: All copyright notices and license texts are preserved in distributions
3. **Source Code Availability**: Links to official repositories are maintained for transparency
4. **Copyleft Obligations**: GPL components (Fail2Ban, iptables) remain under GPL; our automation scripts are separately licensed
5. **Commercial Use**: Most components allow commercial use; Spamhaus requires commercial license for commercial usage beyond personal use

## Special Licensing Considerations

### Fail2Ban Integration
- **Interaction Method**: VoidGuard calls Fail2Ban through its standard command-line interface
- **No Code Modification**: We do not modify Fail2Ban source code
- **Configuration Only**: Our scripts generate standard Fail2Ban configuration files
- **Separate Distribution**: Fail2Ban is installed separately through system package managers

### Threat Intelligence Data
- **Ipsum Project**: Public domain data, freely usable
- **Spamhaus**: Free for non-commercial use; commercial deployments require Spamhaus commercial license
- **Tor Project**: Exit node lists are publicly available data

### Commercial Licensing
For commercial deployments using Spamhaus data, customers must obtain appropriate commercial licenses directly from The Spamhaus Project Ltd.

---

**Last Updated**: January 2025  
**VoidGuard Enhanced Server Protection Version**: 2.1.0  
**Compliance Reviewed**: January 2025

For the most current license information, always refer to the official source repositories listed above.