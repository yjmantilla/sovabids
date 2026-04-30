from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("sovabids")
except PackageNotFoundError:
    __version__ = "unknown"
