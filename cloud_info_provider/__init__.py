import importlib.metadata

try:
    __version__ = importlib.metadata.version(__package__)
except importlib.metadata.PackageNotFoundError:
    # Package not installed in the environment (editable/dev checkout).
    # Fall back to a default version so importing the package doesn't fail
    # during local testing.
    __version__ = "0.0"
