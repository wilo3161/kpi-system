from .manager import get_db_v2 as get_db

def __getattr__(name: str):
    if name == "local_db":
        from .manager import local_db
        return local_db
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["get_db", "local_db"]
