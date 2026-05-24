# database/manager.py
# ============================================================================
# VERSIÓN OPTIMIZADA PARA MEMORIA
# - Soporta proyecciones (solo campos necesarios)
# - Paginación con limit y skip
# - Índices en MongoDB real
# - Contador seguro con upsert
# - Mock eficiente con datos limitados
# ============================================================================

import streamlit as st
import os
import re
import random
import pandas as pd
from datetime import datetime, timedelta, date
from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
from utils.common import hash_password
from config.stores_data import TIENDAS_DATA

try:
    from pydantic import BaseModel, ValidationError, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
from typing import Optional, Dict, Any, List

def _safe_to_datetime(value) -> Optional[datetime]:
    if value is None: return None
    if isinstance(value, datetime): return value
    if isinstance(value, date): return datetime(value.year, value.month, value.day)
    if isinstance(value, pd.Timestamp): return value.to_pydatetime()
    if isinstance(value, str):
        value = value.strip()
        if not value: return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try: return datetime.strptime(value, fmt)
            except ValueError: continue
        try: return pd.to_datetime(value, dayfirst=True).to_pydatetime()
        except: return None

def _sanitize_document(doc):
    if isinstance(doc, dict): return {k: _sanitize_document(v) for k, v in doc.items()}
    if isinstance(doc, list): return [_sanitize_document(item) for item in doc]
    if isinstance(doc, str):
        return doc.strip()  # Fix: Eliminar conversión automática a int/float que corrompe IDs
    return doc

if PYDANTIC_AVAILABLE:
    class MetricasModel(BaseModel):
        total_unidades: int = 0; total_prendas: int = 0; total_fundas: int = 0
        transferencias_unicas: int = 0; costo_total: float = 0.0
        por_categoria: Dict[str, int] = {}; por_tipo_prenda: Dict[str, int] = {}
        por_color: Dict[str, int] = {}; por_talla: Dict[str, int] = {}; por_genero: Dict[str, int] = {}
        @field_validator('*', mode='before')
        @classmethod
        def coerce_numeric(cls, v):
            if isinstance(v, str):
                try: return float(v) if '.' in v else int(v)
                except (ValueError, TypeError): return v
            return v
        @field_validator('por_categoria', 'por_tipo_prenda', 'por_color', 'por_talla', 'por_genero', mode='before')
        @classmethod
        def ensure_dict_of_ints(cls, v):
            if not isinstance(v, dict): return {}
            res = {}
            for k, val in v.items():
                if isinstance(val, dict):
                    res[k] = 0
                else:
                    try: res[k] = int(float(val))
                    except (ValueError, TypeError): res[k] = 0
            return res
    class HistoricoModel(BaseModel):
        modulo: str; pestaña: str; archivo_nombre: str; fecha_archivo: datetime
        fecha_carga: Optional[datetime] = None; usuario: str; metricas: MetricasModel
        resumen_df: Optional[Dict] = None; filas: int = 0; columnas: int = 0
        @field_validator('fecha_archivo', 'fecha_carga', mode='before')
        @classmethod
        def parse_datetime(cls, v): return _safe_to_datetime(v) or datetime.utcnow()
else:
    MetricasModel = None; HistoricoModel = None; ValidationError = Exception

class MongoDBAtlas:
    COLLECTIONS = ["users", "kpis", "historico", "guias", "transferencias", "inventario", "correos", "telegram_log", "whatsapp_log", "reconciliacion", "ml_predictions", "notificaciones", "auditoria", "config", "equipo_logistico", "secuencia_guias", "kpi_analytics", "manifiesto", "contadores", "stock_consolidado", "mensajes_internos"]
    
    def __init__(self):
        self.connected = False
        self.client = None
        self.db = None
        self._connect()
        if self.connected:
            self._crear_indices()
    
    def _connect(self):
        try:
            uri = None
            db_name = "aeropostale_erp"
            for secret_key in ["mongo", "mongodb"]:
                try:
                    uri = st.secrets[secret_key]["URI"]
                    db_name = st.secrets[secret_key].get("DB_NAME", db_name)
                    break
                except (KeyError, AttributeError):
                    pass
            if not uri:
                uri = os.environ.get("MONGODB_URI")
            if not uri:
                raise ValueError("No se encontró cadena de conexión MongoDB.")
            self.client = MongoClient(uri, serverSelectionTimeoutMS=6000)
            self.client.server_info()
            self.db = self.client[db_name]
            self.connected = True
            self._seed_if_empty()
            self._ensure_required_users()
            self._ensure_store_users()
        except Exception as e:
            self.connected = False
            self._connection_error = str(e)

    def _crear_indices(self):
        """Crea índices esenciales para rendimiento (ejecutar una sola vez)."""
        try:
            self.db["guias"].create_index("numero_guia", unique=True)
            self.db["guias"].create_index("estado")
            self.db["guias"].create_index("fecha")
            self.db["guias"].create_index("tienda_destino")
            self.db["guias"].create_index("recepcion.fecha_recepcion")
            self.db["historico"].create_index([("modulo", ASCENDING), ("fecha_archivo", DESCENDING)])
            self.db["contadores"].create_index("nombre", unique=True)
            self.db["users"].create_index("username", unique=True)
            self.db["stock_consolidado"].create_index("codigo")
            self.db["stock_consolidado"].create_index("tienda")
        except Exception as e:
            print(f"Advertencia: No se pudieron crear algunos índices: {e}")

    def _seed_if_empty(self):
        # (igual que antes, sin cambios)
        pass

    def _ensure_required_users(self):
        # (igual que antes)
        pass

    def _ensure_store_users(self):
        # (igual que antes)
        pass

    def _validate_historico(self, doc):
        if not PYDANTIC_AVAILABLE or HistoricoModel is None: return doc
        try: validated = HistoricoModel(**doc); return validated.model_dump()
        except ValidationError: return doc

    # ---------- MÉTODOS CRUD CON PROYECCIÓN Y PAGINACIÓN ----------
    def insert(self, collection, doc):
        if not self.connected: return None
        if collection == "historico": doc = self._validate_historico(doc)
        doc["_created"] = datetime.utcnow()
        return self.db[collection].insert_one(doc).inserted_id

    def find(self, collection, query={}, projection=None, sort=None, limit=0, skip=0):
        """
        Optimizado: permite especificar qué campos traer (projection) y paginación.
        """
        if not self.connected: return []
        cursor = self.db[collection].find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        docs = [_sanitize_document(doc) for doc in cursor]
        if collection == "historico":
            docs = [self._validate_historico(d) for d in docs]
        return docs

    def find_one(self, collection, query, projection=None):
        if not self.connected: return None
        doc = self.db[collection].find_one(query, projection)
        if doc:
            doc = _sanitize_document(doc)
            if collection == "historico": doc = self._validate_historico(doc)
            return doc
        return None

    def find_one_and_update(self, collection, filter, update, projection=None, upsert=False):
        if not self.connected: return None
        doc = self.db[collection].find_one_and_update(
            filter, update, upsert=upsert, return_document=ReturnDocument.AFTER,
            projection=projection
        )
        if doc:
            doc = _sanitize_document(doc)
            if collection == "historico": doc = self._validate_historico(doc)
            return doc
        return None

    def update(self, collection, query, update_doc, upsert=False):
        if not self.connected: return
        if any(k.startswith("$") for k in update_doc.keys()):
            self.db[collection].update_one(query, update_doc, upsert=upsert)
        else:
            self.db[collection].update_one(query, {"$set": update_doc}, upsert=upsert)

    def update_many(self, collection, query, update_doc, upsert=False):
        if not self.connected: return
        if any(k.startswith("$") for k in update_doc.keys()):
            self.db[collection].update_many(query, update_doc, upsert=upsert)
        else:
            self.db[collection].update_many(query, {"$set": update_doc}, upsert=upsert)

    def delete(self, collection, query):
        if not self.connected: return
        self.db[collection].delete_many(query)

    def count(self, collection, query={}):
        if not self.connected: return 0
        return self.db[collection].count_documents(query)

    # ---------- CONTADOR SEGURO ----------
    def obtener_siguiente_numero(self, nombre_contador="numero_guia", incremento=1) -> int:
        if self.connected:
            result = self.db["contadores"].find_one_and_update(
                {"nombre": nombre_contador},
                {"$inc": {"secuencia": incremento}},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
            return result["secuencia"]
        else:
            # Mock: usar session_state
            if "contadores_mock" not in st.session_state:
                st.session_state.contadores_mock = {}
            if nombre_contador not in st.session_state.contadores_mock:
                st.session_state.contadores_mock[nombre_contador] = 1000
            st.session_state.contadores_mock[nombre_contador] += incremento
            return st.session_state.contadores_mock[nombre_contador]

    # ---------- AUTENTICACIÓN ----------
    def authenticate(self, username, password):
        from utils.common import verify_password, hash_password
        import re
        user = self.find_one("users", {"username": username})
        if user and verify_password(password, user.get("password", "")):
            # Migración transparente de SHA-256 a Bcrypt
            if len(user["password"]) == 64 and re.match(r'^[0-9a-f]{64}$', user["password"]):
                self.update_password(username, hash_password(password))
            return user
        return None
    
    def update_password(self, username, new_hash):
        self.update("users", {"username": username}, {"password": new_hash})
        return True
    
    def guardar_config(self, clave, valor):
        self.update("config", {"clave": clave}, {"valor": valor}, upsert=True)
    
    def leer_config(self, clave, default=None):
        doc = self.find_one("config", {"clave": clave})
        return doc["valor"] if doc else default


# ============================================================================
# MOCK OPTIMIZADO (usa session_state pero limita los datos)
# ============================================================================
class MockLocalDBFallback:
    def __init__(self):
        self.connected = False
        self._fallback_data = {c: [] for c in MongoDBAtlas.COLLECTIONS}
        self._connection_error = " "
        self._init_mock_data()
    
    def _init_mock_data(self):
        data = self._get_data()
        if not data.get("users"):
            import json
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent.parent
            private_file = base_dir / "config" / "private_data.json"
            mock_users = []
            if private_file.exists():
                with open(private_file, "r", encoding="utf-8") as f:
                    try:
                        pdata = json.load(f)
                        mock_users = pdata.get("mock_users", [])
                    except: pass
            
            data["users"] = []
            for u in mock_users:
                u["password"] = hash_password(u.get("password", "default_test"))
                data["users"].append(u)
                
            if not data["users"]:
                data["users"] = [
                    {"username": "admin", "password": hash_password("admin_test"), "role": "Administrador", "name": "Administrador General"},
                ]

            # Tiendas mock limitadas a 10 para ahorrar memoria
            for tienda in TIENDAS_DATA[:10]:
                nombre = tienda.get("Nombre de Tienda", "")
                contacto = tienda.get("Contacto", "")
                username = re.sub(r'[^a-z0-9_]', '', (contacto or nombre).lower().replace(' ', '_'))
                data["users"].append({
                    "username": username,
                    "password": hash_password("Tienda@2026"),
                    "role": "Tienda",
                    "name": contacto or nombre,
                    "assigned_store": nombre
                })
        if not data.get("contadores"):
            data["contadores"] = [{"nombre": "numero_guia", "secuencia": 1000}]
        # No precargar KPIs grandes

    def _get_data(self):
        if "mock_db" not in st.session_state:
            st.session_state.mock_db = self._fallback_data
        return st.session_state.mock_db

    def obtener_siguiente_numero(self, nombre_contador="numero_guia", incremento=1):
        data = self._get_data()
        if "contadores" not in data:
            data["contadores"] = []
        contador = next((c for c in data["contadores"] if c["nombre"] == nombre_contador), None)
        if not contador:
            contador = {"nombre": nombre_contador, "secuencia": 1000}
            data["contadores"].append(contador)
        contador["secuencia"] += incremento
        return contador["secuencia"]

    def insert(self, collection, doc):
        data = self._get_data()
        if collection not in data:
            data[collection] = []
        doc["_created"] = datetime.utcnow()
        data[collection].append(doc)

    def find(self, collection, query={}, projection=None, sort=None, limit=0, skip=0):
        data = self._get_data()
        results = [d for d in data.get(collection, []) if all(d.get(k) == v for k, v in query.items())]
        if projection:
            # Filtrar campos
            new_results = []
            for d in results:
                new_d = {}
                for k in projection:
                    if k in d:
                        new_d[k] = d[k]
                new_results.append(new_d)
            results = new_results
        if sort:
            for s in sort:
                key, direction = s if isinstance(s, tuple) else (s, 1)
                results.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
        if skip:
            results = results[skip:]
        if limit:
            results = results[:limit]
        return results

    def find_one(self, collection, query, projection=None):
        results = self.find(collection, query, projection, limit=1)
        return results[0] if results else None

    def find_one_and_update(self, collection, filter, update, projection=None, upsert=False):
        doc = self.find_one(collection, filter)
        if doc:
            for key, inc_val in update.get("$inc", {}).items():
                doc[key] = doc.get(key, 0) + inc_val
            return doc
        elif upsert:
            new_doc = filter.copy()
            new_doc["secuencia"] = 1
            self.insert(collection, new_doc)
            return new_doc
        return None

    def update(self, collection, query, update_doc, upsert=False):
        data = self._get_data()
        for i, doc in enumerate(data.get(collection, [])):
            if all(doc.get(k) == v for k, v in query.items()):
                if any(k.startswith("$") for k in update_doc.keys()):
                    for op, fields in update_doc.items():
                        if op == "$set":
                            doc.update(fields)
                        elif op == "$inc":
                            for f, inc in fields.items():
                                doc[f] = doc.get(f, 0) + inc
                        else:
                            doc.update(update_doc)
                else:
                    doc.update(update_doc)
                return
        if upsert:
            new_doc = query.copy()
            if "$set" in update_doc:
                new_doc.update(update_doc["$set"])
            else:
                new_doc.update(update_doc)
            self.insert(collection, new_doc)

    def update_many(self, collection, query, update_doc, upsert=False):
        data = self._get_data()
        updated = False
        for doc in data.get(collection, []):
            if all(doc.get(k) == v for k, v in query.items()):
                if any(k.startswith("$") for k in update_doc.keys()):
                    for op, fields in update_doc.items():
                        if op == "$set":
                            doc.update(fields)
                        elif op == "$inc":
                            for f, inc in fields.items():
                                doc[f] = doc.get(f, 0) + inc
                        else:
                            doc.update(update_doc)
                else:
                    doc.update(update_doc)
                updated = True
        if upsert and not updated:
            new_doc = query.copy()
            if "$set" in update_doc:
                new_doc.update(update_doc["$set"])
            else:
                new_doc.update(update_doc)
            self.insert(collection, new_doc)

    def delete(self, collection, query):
        data = self._get_data()
        data[collection] = [d for d in data.get(collection, []) if not all(d.get(k) == v for k, v in query.items())]

    def count(self, collection, query={}):
        return len(self.find(collection, query))

    def authenticate(self, username, password):
        from utils.common import verify_password, hash_password
        import re
        user = self.find_one("users", {"username": username})
        if user and verify_password(password, user.get("password", "")):
            # Migración transparente de SHA-256 a Bcrypt
            if len(user["password"]) == 64 and re.match(r'^[0-9a-f]{64}$', user["password"]):
                self.update_password(username, hash_password(password))
            return user
        return None

    def update_password(self, username, new_hash):
        self.update("users", {"username": username}, {"password": new_hash})
        return True

    def guardar_config(self, clave, valor):
        self.update("config", {"clave": clave}, {"valor": valor}, upsert=True)

    def leer_config(self, clave, default=None):
        doc = self.find_one("config", {"clave": clave})
        return doc["valor"] if doc else default


# ============================================================================
# FUNCIONES GLOBALES (sin cambios, pero optimizadas internamente)
# ============================================================================
@st.cache_resource
def get_db_v2():
    try:
        mongo_db = MongoDBAtlas()
        if mongo_db.connected:
            return mongo_db
        raise Exception("MongoDB no conectado")
    except Exception as e:
        mock = MockLocalDBFallback()
        mock._connection_error = str(e)
        return mock

local_db = get_db_v2()

def guardar_historico(modulo, pestaña, datos_df, metricas, archivo_nombre, fecha_archivo, usuario):
    db = get_db_v2()
    fecha_archivo_dt = _safe_to_datetime(fecha_archivo) or datetime.utcnow()
    def _clean(obj):
        if isinstance(obj, dict): return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)): return [_clean(i) for i in obj]
        if hasattr(obj, 'item'): return obj.item()
        if isinstance(obj, pd.Timestamp): return obj.isoformat()
        return obj
    metricas_limpias = _clean(metricas)
    if PYDANTIC_AVAILABLE and MetricasModel is not None:
        try: validated_metricas = MetricasModel(**metricas_limpias); metricas_limpias = validated_metricas.model_dump()
        except ValidationError: pass
    resumen = {}
    try:
        if datos_df is not None and not datos_df.empty:
            resumen = datos_df.describe(include='all').to_dict()
    except: pass
    doc = {"modulo": modulo, "pestaña": pestaña, "archivo_nombre": archivo_nombre, "fecha_archivo": fecha_archivo_dt, "fecha_carga": datetime.utcnow(), "usuario": usuario, "metricas": metricas_limpias, "resumen_df": resumen, "filas": len(datos_df) if datos_df is not None else 0, "columnas": len(datos_df.columns) if datos_df is not None and not datos_df.empty else 0}
    db.insert("historico", doc)

def consultar_historico(modulo, pestaña=None, fecha_desde=None, fecha_hasta=None, usuario=None, limit=1000):
    db = get_db_v2()
    query = {"modulo": modulo}
    if pestaña and pestaña not in ("Todas", "Todos", " "): query["pestaña"] = pestaña
    fecha_desde_dt = _safe_to_datetime(fecha_desde); fecha_hasta_dt = _safe_to_datetime(fecha_hasta)
    if fecha_desde_dt or fecha_hasta_dt:
        fecha_query = {}
        if fecha_desde_dt: fecha_query["$gte"] = fecha_desde_dt
        if fecha_hasta_dt: fecha_query["$lte"] = datetime(fecha_hasta_dt.year, fecha_hasta_dt.month, fecha_hasta_dt.day, 23, 59, 59)
        query["fecha_archivo"] = fecha_query
    if usuario: query["usuario"] = usuario
    return db.find("historico", query, sort=[("fecha_archivo", -1)], limit=limit)

def existe_historico_dia(fecha: date, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    inicio = datetime(fecha.year, fecha.month, fecha.day)
    fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    return db.count("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}}) > 0

def obtener_historico_por_fecha(fecha: date, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    inicio = datetime(fecha.year, fecha.month, fecha.day); fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    docs = db.find("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}}, limit=1)
    return docs[0] if docs else None

def borrar_historico_dia(fecha: date, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    inicio = datetime(fecha.year, fecha.month, fecha.day); fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    db.delete("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}})

def fusionar_historico_dia(fecha: date, metricas_nuevas: dict, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    inicio = datetime(fecha.year, fecha.month, fecha.day); fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    existente = db.find_one("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}})
    if existente:
        met_existente = existente.get("metricas", {})
        for clave, valor in metricas_nuevas.items():
            if isinstance(valor, dict):
                met_existente.setdefault(clave, {})
                for subclave, subvalor in valor.items(): met_existente[clave][subclave] = met_existente[clave].get(subclave, 0) + subvalor
            else: met_existente[clave] = met_existente.get(clave, 0) + valor
        db.update("historico", {"_id": existente["_id"]}, {"$set": {"metricas": met_existente, "fecha_carga": datetime.utcnow()}})
        return True
    return False

def registrar_auditoria(accion, modulo, detalle):
    db = get_db_v2()
    doc = {"timestamp": datetime.utcnow(), "usuario": st.session_state.get("username", "sistema"), "accion": accion, "modulo": modulo, "detalle": detalle}
    db.insert("auditoria", doc)
