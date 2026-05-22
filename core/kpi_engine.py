# MODIFIED: 2026-05-21 - Unified cache TTL to 300s, added cobertura_inventario, added batch_otif_evolution
"""
Motor de KPIs del ERP Aeropostale.
Proporciona indicadores en tiempo real sobre la operación logística.
Soporta tanto MongoDB Atlas como el fallback mock.
"""

import streamlit as st
from datetime import datetime, timedelta
from database.manager import local_db
from utils.common import sanitize_for_mongo


class KPIEngine:
    def __init__(self):
        self.db = local_db

    def invalidate_cache(self) -> None:
        """Limpia la caché de Streamlit para forzar el recálculo de KPIs."""
        st.cache_data.clear()

    # ------------------------------------------------------------------
    # Helper para pipelines en mock (sin aggregate)
    # ------------------------------------------------------------------
    def _aggregate_fallback(
        self, collection: str, pipeline: list, default: any = None
    ) -> any:
        """
        Intenta ejecutar un pipeline de agregación en MongoDB.
        Si la colección no soporta aggregate (mock fallback), retorna default.
        """
        if not self.db.connected or not hasattr(self.db, "db"):
            return default
        try:
            return list(self.db.db[collection].aggregate(pipeline))
        except Exception:
            return default

    # ------------------------------------------------------------------
    # KPIs CORE
    # ------------------------------------------------------------------
    @st.cache_data(ttl=300)
    def recepciones_hoy(_self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        pipeline = [
            {"$match": {"recepcion.fecha_recepcion": {"$regex": f"^{hoy}"}}},
            {"$count": "total"}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result:
            return sanitize_for_mongo(result[0].get("total", 0))
        # Fallback manual si no hay aggregate
        guias = _self.db.find("guias", {"recepcion.fecha_recepcion": {"$regex": f"^{hoy}"}})
        return len(guias)

    @st.cache_data(ttl=300)
    def guias_emitidas_hoy(_self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        return _self.db.count("guias", {"fecha": {"$regex": f"^{hoy}"}})

    @st.cache_data(ttl=300)
    def otif(_self, dias=30):
        desde = (datetime.now() - timedelta(days=dias)).isoformat()
        total = _self.db.count("guias", {"fecha": {"$gte": desde}})
        if total == 0:
            return 0.0

        # Recibidas conformes = recepcion.estado_recepcion == "CONFORME"
        pipeline = [
            {"$match": {
                "recepcion.estado_recepcion": "CONFORME",
                "recepcion.fecha_recepcion": {"$gte": desde}
            }},
            {"$count": "recibidas_ok"}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result:
            recibidas_ok = sanitize_for_mongo(result[0].get("recibidas_ok", 0))
        else:
            # Fallback manual
            guias = _self.db.find("guias", {
                "recepcion.estado_recepcion": "CONFORME",
                "recepcion.fecha_recepcion": {"$gte": desde}
            })
            recibidas_ok = len(guias)

        return (recibidas_ok / total) * 100

    @st.cache_data(ttl=300)
    def otif_evolution_batch(_self, dias=30):
        """
        Obtiene la evolución OTIF para los últimos N días en UNA sola consulta,
        agrupando por día. Retorna (fechas, valores_otif).
        """
        desde = (datetime.now() - timedelta(days=dias)).isoformat()
        # Agregación: grup por día de fecha de guía para total y día de recepción conforme
        pipeline = [
            {"$match": {"fecha": {"$gte": desde}, "anulada": {"$ne": True}}},
            {"$group": {
                "_id": {"$substr": ["$fecha", 0, 10]},
                "total": {"$sum": 1},
                "conformes": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$recepcion.estado_recepcion", "CONFORME"]},
                                {"$ne": ["$recepcion.fecha_recepcion", None]}
                            ]},
                            1, 0
                        ]
                    }
                }
            }},
            {"$sort": {"_id": 1}}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result:
            fechas = []
            valores = []
            for r in result:
                total = sanitize_for_mongo(r.get("total", 0))
                conformes = sanitize_for_mongo(r.get("conformes", 0))
                fechas.append(r["_id"])
                valores.append((conformes / total * 100) if total > 0 else 0.0)
            return fechas, valores

        # Fallback: iterar días manualmente
        fechas = []
        valores = []
        for i in range(1, dias + 1):
            d = (datetime.now() - timedelta(days=dias - i)).strftime("%Y-%m-%d")
            fechas.append(d)
            v = _self.otif(dias=i)
            valores.append(v if i > 0 else 0)
        return fechas, valores

    @st.cache_data(ttl=300)
    def tiempo_promedio_recepcion(_self, dias=30):
        desde = (datetime.now() - timedelta(days=dias)).isoformat()
        pipeline = [
            {"$match": {
                "recepcion.fecha_recepcion": {"$gte": desde},
                "fecha": {"$gte": desde}
            }},
            {"$project": {
                "diff_horas": {
                    "$divide": [
                        {"$subtract": [
                            {"$toDate": "$recepcion.fecha_recepcion"},
                            {"$toDate": "$fecha"}
                        ]},
                        3600000
                    ]
                }
            }},
            {"$group": {
                "_id": None,
                "prom_horas": {"$avg": "$diff_horas"}
            }}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result:
            return round(sanitize_for_mongo(result[0]["prom_horas"]), 1)
        return 0.0

    @st.cache_data(ttl=300)
    def tasa_faltantes(_self, dias=30):
        desde = (datetime.now() - timedelta(days=dias)).isoformat()
        pipeline = [
            {"$match": {
                "recepcion.diferencias.tiene_diferencias": True,
                "fecha": {"$gte": desde}
            }},
            {"$group": {
                "_id": None,
                "total_esperado": {"$sum": "$recepcion.diferencias.total_esperado"},
                "total_faltantes": {"$sum": {"$sum": "$recepcion.diferencias.faltantes.faltante"}}
            }}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result and result[0]["total_esperado"] > 0:
            return (result[0]["total_faltantes"] / result[0]["total_esperado"]) * 100
        return 0.0

    @st.cache_data(ttl=300)
    def cobertura_inventario(_self):
        """
        Tasa de Cobertura de Inventario = (stock disponible / ventas promedio diarias) * 30
        Calculado desde la colección 'inventario' e 'historico'.
        """
        try:
            # Obtener stock disponible total de inventario
            inv_pipeline = [
                {"$group": {
                    "_id": None,
                    "stock_total": {"$sum": "$cantidad"}
                }}
            ]
            inv_result = _self._aggregate_fallback("inventario", inv_pipeline, [])
            if inv_result and inv_result[0].get("stock_total", 0) > 0:
                stock_total = sanitize_for_mongo(inv_result[0]["stock_total"])
            else:
                # Fallback: sumar desde find
                inventarios = _self.db.find("inventario", {})
                stock_total = sum(i.get("cantidad", 0) for i in inventarios)

            # Obtener ventas promedio diarias desde histórico (últimos 30 días)
            desde = (datetime.now() - timedelta(days=30)).isoformat()
            hist = _self.db.find("historico", {"fecha_archivo": {"$gte": desde}})
            total_ventas = 0
            for h in hist:
                met = h.get("metricas", {})
                total_ventas += met.get("total_unidades", 0) if isinstance(met, dict) else 0

            ventas_prom_diarias = total_ventas / 30.0 if total_ventas > 0 else 1
            cobertura = (stock_total / ventas_prom_diarias) * 30
            return round(cobertura, 1)
        except Exception:
            return 0.0

    @st.cache_data(ttl=300)
    def top_tiendas_incidencias(_self, dias=30, limit=10):
        desde = (datetime.now() - timedelta(days=dias)).isoformat()
        pipeline = [
            {"$unwind": "$incidencias"},
            {"$match": {"incidencias.fecha": {"$gte": desde}}},
            {"$group": {"_id": "$tienda_destino", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result:
            return [{"_id": r["_id"], "count": r["count"]} for r in result]
        # Fallback manual
        from collections import Counter
        guias = _self.db.find("guias", {"incidencias.fecha": {"$gte": desde}})
        cnt = Counter()
        for g in guias:
            for inc in g.get("incidencias", []):
                if inc.get("fecha", "") >= desde:
                    cnt[g.get("tienda_destino", "Desconocida")] += 1
        top = cnt.most_common(limit)
        return [{"_id": k, "count": v} for k, v in top]

    @st.cache_data(ttl=300)
    def distribucion_incidencias(_self, dias=30):
        desde = (datetime.now() - timedelta(days=dias)).isoformat()
        pipeline = [
            {"$unwind": "$incidencias"},
            {"$match": {"incidencias.fecha": {"$gte": desde}}},
            {"$group": {"_id": "$incidencias.tipo", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = _self._aggregate_fallback("guias", pipeline, [])
        if result:
            return [{"_id": r["_id"], "count": r["count"]} for r in result]
        # Fallback manual
        from collections import Counter
        guias = _self.db.find("guias", {"incidencias.fecha": {"$gte": desde}})
        cnt = Counter()
        for g in guias:
            for inc in g.get("incidencias", []):
                if inc.get("fecha", "") >= desde:
                    cnt[inc.get("tipo", "Otro")] += 1
        return [{"_id": k, "count": v} for k, v in cnt.most_common()]

    def resumen_ejecutivo(self):
        return {
            "recepciones_hoy": self.recepciones_hoy(),
            "guias_emitidas_hoy": self.guias_emitidas_hoy(),
            "otif_30d": self.otif(30),
            "tiempo_promedio_30d": self.tiempo_promedio_recepcion(30),
            "tasa_faltantes_30d": self.tasa_faltantes(30),
            "cobertura_inventario": self.cobertura_inventario(),
        }
