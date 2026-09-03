# load_tiendas.py
"""
Cargador de tiendas iniciales para la base de datos y catálogo del sistema.
"""
from automation.tiendas_data import TIENDAS_DATA as tiendas_data

if __name__ == "__main__":
    from database.manager import local_db
    existentes = local_db.find("tiendas", {})
    if not existentes:
        print("Cargando tiendas a la base de datos...")
        for t in tiendas_data:
            local_db.insert("tiendas", t)
        print(f"Se cargaron {len(tiendas_data)} tiendas exitosamente.")
    else:
        print(f"Las tiendas ya existen en la BD ({len(existentes)} registradas).")
