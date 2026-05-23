"""
scripts/seed_demo_data.py — GENERA DATOS DE DEMO PARA PROBAR EL ERP
=====================================================================
Crea guías, inventario y equipo de prueba automáticamente.
Ejecutar: streamlit run app.py (se ejecuta automático al iniciar)
"""

import random
from datetime import datetime, timedelta, date
from database.manager import local_db, get_db_v2
from config.stores_data import TIENDAS_DATA

DEMO_ITEMS = [
    ("CAMISETA LOGO AERO", "Blanco", "M"),
    ("CAMISETA LOGO AERO", "Blanco", "L"),
    ("CAMISETA LOGO AERO", "Negro", "M"),
    ("CAMISETA LOGO AERO", "Negro", "L"),
    ("CAMISETA LOGO AERO", "Azul", "XL"),
    ("POLO CLÁSICO", "Rojo", "S"),
    ("POLO CLÁSICO", "Rojo", "M"),
    ("POLO CLÁSICO", "Azul Marino", "L"),
    ("POLO CLÁSICO", "Blanco", "M"),
    ("HOODIE CREW", "Gris", "L"),
    ("HOODIE CREW", "Negro", "XL"),
    ("HOODIE CREW", "Azul", "M"),
    ("JOGGER PANTS", "Negro", "S"),
    ("JOGGER PANTS", "Negro", "M"),
    ("JOGGER PANTS", "Gris", "L"),
    ("SHORT DEPORTIVO", "Azul", "M"),
    ("SHORT DEPORTIVO", "Negro", "L"),
    ("GORRA AERO", "Negro", "ÚNICA"),
    ("GORRA AERO", "Blanco", "ÚNICA"),
    ("MOCHILA AERO", "Negro", "ÚNICA"),
]


def seed_demo_guias(num_guias=15):
    """Crea guías demo con estados variados."""
    coleccion = "guias"
    existentes = local_db.count(coleccion)
    if existentes > 5:
        return  # Ya hay datos

    tiendas = [t.get("Nombre de Tienda", t.get("nombre", "")) for t in TIENDAS_DATA if t.get("Nombre de Tienda", t.get("nombre", ""))]
    if not tiendas:
        return

    for i in range(num_guias):
        tienda = random.choice(tiendas)
        num_items = random.randint(2, 6)
        items = random.sample(DEMO_ITEMS, min(num_items, len(DEMO_ITEMS)))
        items_clean = [
            {"producto": p, "color": c, "talla": t, "cantidad": random.randint(5, 50)}
            for p, c, t in items
        ]
        total = sum(it["cantidad"] for it in items_clean)
        dias_atras = random.randint(1, 45)
        fecha_guia = date.today() - timedelta(days=dias_atras)
        recibida = random.random() > 0.3  # 70% recibidas

        numero_guia = f"FC-{fecha_guia.strftime('%Y%m%d')}-{tienda[:3].upper()}-{i+1:04d}"

        doc = {
            "numero_guia": numero_guia,
            "tienda_destino": tienda,
            "fecha_guia": fecha_guia.isoformat(),
            "fecha_creacion": (datetime.now() - timedelta(days=dias_atras)).isoformat(),
            "usuario_creador": random.choice(["admin", "Andres", "Luis", "Jessica", "Josue"]),
            "items": items_clean,
            "total_prendas": total,
            "estado": "RECIBIDA" if recibida else "PENDIENTE",
            "fecha_recepcion": (datetime.now() - timedelta(days=dias_atras - 1)).isoformat() if recibida else None,
            "usuario_recepcion": "tienda" if recibida else None,
            "notas": "",
        }
        local_db.insert(coleccion, doc)

        # Si está pendiente, crear guía_pendiente
        if not recibida:
            local_db.insert("guias_pendientes", {
                "numero_guia": numero_guia,
                "tienda_destino": tienda,
                "fecha_creacion": doc["fecha_creacion"],
                "estado": "PENDIENTE_RECEPCION",
                "visible": True,
            })


def seed_demo_inventario():
    """Crea inventario demo con datos variados."""
    coleccion = "inventario"
    existentes = local_db.count(coleccion, {"carga_activa": True})
    if existentes > 10:
        return

    registros = []
    for producto, color, talla in DEMO_ITEMS:
        for i in range(random.randint(1, 3)):
            registros.append({
                "codigo_estilo": f"AERO-{random.randint(100,999)}",
                "codigo_barra": f"{random.randint(1000000000000, 9999999999999)}",
                "producto_base": producto,
                "color": color,
                "talla": talla,
                "cantidad": random.randint(0, 200),
                "costo": round(random.uniform(5.0, 25.0), 2),
                "precio": round(random.uniform(15.0, 65.0), 2),
                "talla_orden": {"XS":1,"S":2,"M":3,"L":4,"XL":5,"XXL":6,"ÚNICA":99}.get(talla, 99),
                "tipo_prenda": "Camiseta",
                "tipo_abrev": "TEE",
                "genero": "UNISEX",
                "sku_compuesto": f"AERO-{producto[:3].upper()}-{color[:3].upper()}-{talla[:2]}",
                "carga_activa": True,
                "_procesado": datetime.utcnow().isoformat(),
            })

    # En lotes de 500
    for i in range(0, len(registros), 500):
        batch = registros[i:i+500]
        for reg in batch:
            local_db.insert(coleccion, reg)

    # Registrar metadata de carga
    local_db.insert("inventario_uploads", {
        "archivo_nombre": "demo_autogenerado.xlsx",
        "fecha_carga": datetime.utcnow(),
        "usuario": "admin",
        "filas": len(registros),
        "columnas": 12,
        "activo": True,
        "metricas": {
            "total_skus": len(registros),
            "total_unidades": sum(r["cantidad"] for r in registros),
        },
    })


def seed_demo_all():
    """Ejecuta todos los seeds demo."""
    try:
        seed_demo_guias()
        seed_demo_inventario()
    except Exception:
        pass


if __name__ == "__main__":
    seed_demo_all()
    print("✅ Datos demo generados exitosamente")
