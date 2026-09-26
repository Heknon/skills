"""quickcfg: load settings from a file and the environment.

Supported files: TOML, JSON and INI.
"""

from quickcfg.loader import UnsupportedFormat, load

__version__ = "3.1.0"
__all__ = ["load", "UnsupportedFormat"]
