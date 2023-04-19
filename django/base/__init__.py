import importlib

__all__ = [
    'web',
    'tools',
]


def __getattr__(name):
    """Lazy import

    https://peps.python.org/pep-0562/#rationale
    """
    if name in __all__:
        return importlib.import_module("." + name, __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
