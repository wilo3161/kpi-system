import sys
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent))

from database.manager import local_db

def reset_db():
    if not getattr(local_db, 'connected', False):
        st.error("ERROR: No se pudo conectar a MongoDB.")
        return

    colecciones_a_limpiar = [
        "guias", "historico", "kpi_analytics", "discrepancias", 
        "ingresos_no_esperados", "stock_bloqueado", "reconciliacion", 
        "secuencia_guias", "manifiesto", "stock_consolidado", "tiendas"
    ]

    for col in colecciones_a_limpiar:
        local_db.delete(col, {})
        st.write(f"Colección '{col}' vaciada exitosamente.")

    local_db.db["contadores"].update_one(
        {"nombre": "numero_guia"},
        {"$set": {"secuencia": 999}},
        upsert=True
    )
    st.success("Contador 'numero_guia' reseteado a 999 (la primera guía será la 1000).")

reset_db()

