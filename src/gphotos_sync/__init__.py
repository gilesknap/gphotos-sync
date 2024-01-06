from importlib.metadata import version  # noqa

__version__ = version("gphotos-sync")
del version

__all__ = ["__version__"]
