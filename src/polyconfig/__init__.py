from importlib.metadata import PackageNotFoundError, version

from .polyconfig import Config, DotTreeConfig, Inherited, Missing, MissingEnvsError, strautocast

__title__ = "polyconfig"

try:
    __version__ = version(__title__)
except PackageNotFoundError:
    __version__ = "0.0.0"

__author__ = "Kamil Cyganowski"
__license__ = "MIT"
__copyright__ = "Copyright 2026 Kamil Cyganowski"
__all__ = [
    "Config",
    "DotTreeConfig",
    "Inherited",
    "Missing",
    "MissingEnvsError",
    "strautocast",
]
