"""
nas_tools package bootstrap.

Provides access to the WD My Cloud discovery and mount helpers.
"""

from importlib import import_module
from typing import Any

__author__ = "Jason LaTorre"
__version__ = "1.0.0"
__all__ = ["wd_discovery", "wd_mount", "__author__", "__version__"]


def __getattr__(name: str) -> Any:
    """Lazily expose sibling modules to prevent circular imports."""
    if name not in {"wd_discovery", "wd_mount"}:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{name}")
    globals()[name] = module
    return module
