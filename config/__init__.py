# config/__init__.py
from .mongodb import MongoDB, inicializar_datos_base, get_database

__all__ = ['MongoDB', 'inicializar_datos_base', 'get_database']