from database.manager import local_db
import sys

docs = local_db.find('historico', {'modulo': 'dashboard_logistico'}, limit=5)
for d in docs:
    fecha = d.get('fecha_archivo')
    met = d.get('metricas', {})
    pc = met.get('por_categoria', {})
    print(f"Fecha: {fecha}")
    print(f"por_categoria: {pc}")
