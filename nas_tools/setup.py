from pathlib import Path

from setuptools import find_packages, setup

BASE_DIR = Path(__file__).resolve().parent
ABOUT: dict = {}
exec((BASE_DIR / "nas_tools" / "__init__.py").read_text(encoding="utf-8"), ABOUT)

setup(
    name="nas_tools",
    version=ABOUT.get("__version__", "1.0.0"),
    author="Jason LaTorre",
    author_email="support@example.com",
    description="WD My Cloud discovery and SMB mounting tools",
    long_description=(
        "Utilities for discovering Western Digital My Cloud NAS devices and mounting "
        "their SMB shares across Windows, macOS, and Linux."
    ),
    long_description_content_type="text/plain",
    url="https://example.com/nas_tools",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: System :: Networking",
        "Topic :: Utilities",
        "Intended Audience :: System Administrators",
    ],
    entry_points={
        "console_scripts": [
            "wd-discovery=nas_tools.wd_discovery:main",
            "wd-mount=nas_tools.wd_mount:main",
        ]
    },
)*** End Patch
