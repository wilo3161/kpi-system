import logging
logger = logging.getLogger(__name__)

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
# from config.stores_data import TIENDAS_DATA  # Removido para evitar circular import

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
    try:
        from bson.objectid import ObjectId
        if isinstance(doc, ObjectId):
            return str(doc)
    except ImportError:
        pass
    return doc

if PYDANTIC_AVAILABLE:
    class MetricasModel(BaseModel):
        total_unidades: int = 0; total_prendas: int = 0; total_fundas: int = 0
        transferencias_unicas: int = 0; costo_total: float = 0.0
        por_categoria: Dict[str, int] = {}; por_tipo_prenda: Dict[str, int] = {}
        tiendas_activas_por_categoria: Dict[str, int] = {}
        por_color: Dict[str, int] = {}; por_talla: Dict[str, int] = {}; por_genero: Dict[str, int] = {}
        @field_validator('*', mode='before')
        @classmethod
        def coerce_numeric(cls, v):
            if isinstance(v, str):
                try: return float(v) if '.' in v else int(v)
                except (ValueError, TypeError): return v
            return v
        @field_validator('por_categoria', 'por_tipo_prenda', 'tiendas_activas_por_categoria', 'por_color', 'por_talla', 'por_genero', mode='before')
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
    COLLECTIONS = ["users", "kpis", "historico", "guias", "transferencias", "fact_transferencias", "config_estandares", "inventario", "correos", "telegram_log", "whatsapp_log", "reconciliacion", "ml_predictions", "notificaciones", "auditoria", "config", "equipo_logistico", "secuencia_guias", "kpi_analytics", "manifiesto", "contadores", "stock_consolidado", "mensajes_internos", "tiendas"]
    
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
            self.db["historico"].create_index([("modulo", ASCENDING), ("pestaña", ASCENDING), ("fecha_archivo", DESCENDING)])
            self.db["fact_transferencias"].create_index("hash_registro", unique=True)
            self.db["fact_transferencias"].create_index([("fecha_transferencia", ASCENDING), ("transferidor", ASCENDING)])
            self.db["fact_transferencias"].create_index("tienda")
            self.db["fact_transferencias"].create_index("numero_transferencia")
            self.db["config_estandares"].create_index("categoria", unique=True)
            self.db["contadores"].create_index("nombre", unique=True)
            self.db["users"].create_index("username", unique=True)
            self.db["stock_consolidado"].create_index("codigo")
            self.db["stock_consolidado"].create_index("tienda")
            self.db["tiendas"].create_index("Nombre de Tienda", unique=True)
        except Exception as e:
            logger.info(f"Advertencia: No se pudieron crear algunos índices: {e}")

    def _seed_if_empty(self):
        """Puebla tiendas y configuración inicial si MongoDB está vacío."""
        try:
            if self.count("tiendas") == 0:
                from automation.tiendas_data import TIENDAS_DATA
                for t in TIENDAS_DATA:
                    self.insert("tiendas", t)
        except Exception as e:
            logger.info(f"Advertencia al poblar tiendas en MongoDB: {e}")

    def _ensure_required_users(self):
        # Crear usuario admin si no existe
        from utils.common import hash_password
        if self.count("users") == 0 or not self.find_one("users", {"username": "admin"}):
            self.insert("users", {
                "username": "admin",
                "password": hash_password("admin_test"),
                "role": "Administrador",
                "name": "Administrador General"
            })
            
    def _ensure_store_users(self):
        from utils.common import hash_password
        import re
        # Tiendas mock limitadas
        tiendas = ["MALL DEL SOL", "CONDADO SHOPPING", "QUICENTRO"]
        for tienda in tiendas:
            username = re.sub(r'[^a-z0-9_]', '', tienda.lower().replace(' ', '_'))
            if self.count("users", {"username": username}) == 0:
                self.insert("users", {
                    "username": username,
                    "password": hash_password("Tienda@2026"),
                    "role": "Tienda",
                    "name": tienda,
                    "assigned_store": tienda
                })

    def _validate_historico(self, doc):
        if not PYDANTIC_AVAILABLE or HistoricoModel is None: return doc
        try: validated = HistoricoModel(**doc); return validated.model_dump()
        except ValidationError: return doc

    # ---------- MÉTODOS CRUD CON PROYECCIÓN Y PAGINACIÓN ----------
    def insert(self, collection, doc):
        if not self.connected: return None
        try:
            if collection == "historico": doc = self._validate_historico(doc)
            doc["_created"] = datetime.utcnow()
            return self.db[collection].insert_one(doc).inserted_id
        except Exception as e:
            logger.info(f"Error insert {collection}: {e}")
            return None

    def insert_many(self, collection, docs):
        """Inserción masiva de documentos."""
        if not self.connected or not docs: return []
        if collection == "historico": docs = [self._validate_historico(d) for d in docs]
        now = datetime.utcnow()
        for doc in docs:
            doc["_created"] = now
        try:
            return self.db[collection].insert_many(docs).inserted_ids
        except Exception as e:
            return []

    def find(self, collection, query={}, projection=None, sort=None, limit=0, skip=0):
        """
        Optimizado: permite especificar qué campos traer (projection) y paginación.
        """
        if not self.connected: return []
        try:
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
        except Exception as e:
            logger.info(f"Error find {collection}: {e}")
            return []

    def find_one(self, collection, query, projection=None):
        if not self.connected: return None
        try:
            doc = self.db[collection].find_one(query, projection)
            if doc:
                doc = _sanitize_document(doc)
                if collection == "historico": doc = self._validate_historico(doc)
                return doc
            return None
        except Exception as e:
            logger.info(f"Error find_one {collection}: {e}")
            return None

    def find_one_and_update(self, collection, filter, update, projection=None, upsert=False):
        if not self.connected: return None
        try:
            doc = self.db[collection].find_one_and_update(
                filter, update, upsert=upsert, return_document=ReturnDocument.AFTER,
                projection=projection
            )
            if doc:
                doc = _sanitize_document(doc)
                if collection == "historico": doc = self._validate_historico(doc)
                return doc
            return None
        except Exception as e:
            logger.info(f"Error find_one_and_update {collection}: {e}")
            return None

    def update(self, collection, query, update_doc, upsert=False):
        if not self.connected: return
        try:
            if any(k.startswith("$") for k in update_doc.keys()):
                self.db[collection].update_one(query, update_doc, upsert=upsert)
            else:
                self.db[collection].update_one(query, {"$set": update_doc}, upsert=upsert)
        except Exception as e:
            logger.info(f"Error update {collection}: {e}")

    def update_many(self, collection, query, update_doc, upsert=False):
        if not self.connected: return
        try:
            if any(k.startswith("$") for k in update_doc.keys()):
                self.db[collection].update_many(query, update_doc, upsert=upsert)
            else:
                self.db[collection].update_many(query, {"$set": update_doc}, upsert=upsert)
        except Exception as e:
            logger.info(f"Error update_many {collection}: {e}")

    def delete(self, collection, query):
        if not self.connected: return
        try:
            self.db[collection].delete_many(query)
        except Exception as e:
            logger.info(f"Error delete {collection}: {e}")

    def count(self, collection, query={}):
        if not self.connected: return 0
        try:
            return self.db[collection].count_documents(query)
        except Exception as e:
            logger.info(f"Error count {collection}: {e}")
            return 0

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
# MOCK OPTIMIZADO (con soporte para operadores Mongo, iframes y fallback offline)
# ============================================================================
class MockCollection:
    """Emula una colección de PyMongo para compatibilidad con llamadas tipo db['col']."""
    def __init__(self, db_instance, name: str):
        self.db = db_instance
        self.name = name

    def create_index(self, *args, **kwargs):
        pass

    def insert_one(self, doc):
        class Result:
            def __init__(self, _id): self.inserted_id = _id
        self.db.insert(self.name, doc)
        return Result(doc.get("_id", "mock_id"))

    def insert_many(self, docs):
        class Result:
            def __init__(self, ids): self.inserted_ids = ids
        return Result(self.db.insert_many(self.name, docs))

    def find(self, query={}, projection=None, **kwargs):
        return self.db.find(self.name, query, projection, **kwargs)

    def find_one(self, query={}, projection=None, **kwargs):
        return self.db.find_one(self.name, query, projection)

    def find_one_and_update(self, filter, update, projection=None, upsert=False):
        return self.db.find_one_and_update(self.name, filter, update, projection, upsert)

    def update_one(self, query, update_doc, upsert=False):
        return self.db.update(self.name, query, update_doc, upsert)

    def update_many(self, query, update_doc, upsert=False):
        return self.db.update_many(self.name, query, update_doc, upsert)

    def delete_many(self, query):
        return self.db.delete(self.name, query)

    def count_documents(self, query={}):
        return self.db.count(self.name, query)

    def aggregate(self, pipeline):
        return []

    def drop(self):
        self.db.delete(self.name, {})


class MockLocalDBFallback:
    def __init__(self):
        self.connected = False
        self._fallback_data = {c: [] for c in MongoDBAtlas.COLLECTIONS}
        self._connection_error = " "
        self.db = self  # Permite self.db['tiendas'] sin error
        self._init_mock_data()

    def __getitem__(self, collection: str):
        return MockCollection(self, collection)

    def _init_mock_data(self):
        data = self._get_data()
        if not data.get("users"):
            import json
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent.parent
            private_file = base_dir / "config" / "private_data.json"
            mock_users = []
            tiendas_list = []
            if private_file.exists():
                try:
                    with open(private_file, "r", encoding="utf-8-sig") as f:
                        pdata = json.load(f)
                        mock_users = pdata.get("mock_users", [])
                        tiendas_list = pdata.get("tiendas", [])
                except Exception:
                    pass

            data["users"] = []
            for u in mock_users:
                # Guardar usuarios mock con sus contraseñas hasheadas
                data["users"].append({
                    "username": u.get("username", "user"),
                    "password": hash_password(u.get("password", "default_test")),
                    "role": u.get("role", "Usuario"),
                    "name": u.get("name", u.get("username", "Usuario")),
                    "assigned_store": u.get("assigned_store")
                })

            if not any(u.get("username") == "admin" for u in data["users"]):
                data["users"].append({
                    "username": "admin",
                    "password": hash_password("wilo3161"),
                    "role": "Administrador",
                    "name": "Administrador General"
                })

            # Cargar tiendas si no están
            if not data.get("tiendas"):
                if not tiendas_list:
                    try:
                        from automation.tiendas_data import TIENDAS_DATA
                        tiendas_list = list(TIENDAS_DATA)
                    except Exception:
                        pass
                data["tiendas"] = list(tiendas_list)

            # Crear usuarios automáticos para las tiendas
            for tienda in (data.get("tiendas") or [])[:45]:
                nombre = tienda.get("Nombre de Tienda", "")
                contacto = tienda.get("Contacto", "")
                username = re.sub(r'[^a-z0-9_]', '', (contacto or nombre).lower().replace(' ', '_'))
                if not any(u.get("username") == username for u in data["users"]):
                    data["users"].append({
                        "username": username,
                        "password": hash_password("Tienda@2026"),
                        "role": "Tienda",
                        "name": contacto or nombre,
                        "assigned_store": nombre
                    })

        if not data.get("contadores"):
            data["contadores"] = [{"nombre": "numero_guia", "secuencia": 1000}]

    def _get_data(self):
        try:
            if "mock_db" not in st.session_state:
                st.session_state.mock_db = self._fallback_data
            return st.session_state.mock_db
        except Exception:
            return self._fallback_data

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

    def insert_many(self, collection, docs):
        if not docs: return []
        data = self._get_data()
        if collection not in data:
            data[collection] = []
        now = datetime.utcnow()
        for doc in docs:
            doc["_created"] = now
        data[collection].extend(docs)
        return list(range(len(docs)))

    @staticmethod
    def _get_nested(doc, key):
        """Soporta acceso por notación de punto (ej. 'recepcion.fecha_recepcion')."""
        if not isinstance(doc, dict):
            return None
        if "." not in key:
            return doc.get(key)
        parts = key.split(".")
        curr = doc
        for p in parts:
            if isinstance(curr, dict):
                curr = curr.get(p)
            else:
                return None
        return curr

    @staticmethod
    def _match_val(val, cond):
        """Evalúa igualdad directa u operadores de MongoDB ($gte, $lte, $gt, $lt, $ne, $in, $nin, $regex)."""
        if not isinstance(cond, dict):
            return val == cond
        for op, target in cond.items():
            if op == "$gte":
                if val is None or val < target: return False
            elif op == "$lte":
                if val is None or val > target: return False
            elif op == "$gt":
                if val is None or val <= target: return False
            elif op == "$lt":
                if val is None or val >= target: return False
            elif op == "$ne":
                if val == target: return False
            elif op == "$in":
                if val not in target: return False
            elif op == "$nin":
                if val in target: return False
            elif op == "$regex":
                if val is None or not re.search(str(target), str(val)): return False
        return True

    def find(self, collection, query={}, projection=None, sort=None, limit=0, skip=0):
        data = self._get_data()
        items = data.get(collection, [])
        if query:
            results = [
                d for d in items
                if all(self._match_val(self._get_nested(d, k), v) for k, v in query.items())
            ]
        else:
            results = list(items)

        if projection:
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
                results.sort(key=lambda x: str(self._get_nested(x, key) or ""), reverse=(direction == -1))

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
        for doc in data.get(collection, []):
            if all(self._match_val(self._get_nested(doc, k), v) for k, v in query.items()):
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
            if all(self._match_val(self._get_nested(doc, k), v) for k, v in query.items()):
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
        if not query:
            data[collection] = []
        else:
            data[collection] = [
                d for d in data.get(collection, [])
                if not all(self._match_val(self._get_nested(d, k), v) for k, v in query.items())
            ]

    def count(self, collection, query={}):
        return len(self.find(collection, query))

    def authenticate(self, username, password):
        from utils.common import verify_password, hash_password
        user = self.find_one("users", {"username": username})
        if user and verify_password(password, user.get("password", "")):
            # Migración transparente de SHA-256 a Bcrypt
            if len(user["password"]) == 64 and re.match(r'^[0-9a-f]{64}$', user["password"]):
                self.update_password(username, hash_password(password))
            return user
        # Compatibilidad de emergencia para credenciales maestras admin
        if username == "admin" and password in ("wilo3161", "admin123", "admin_test"):
            if not user:
                user = {
                    "username": "admin",
                    "password": hash_password(password),
                    "role": "Administrador",
                    "name": "Administrador General"
                }
                self.insert("users", user)
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

def _safe_to_date(f):
    if isinstance(f, datetime): return f.date()
    if isinstance(f, date): return f
    if isinstance(f, str):
        try: return pd.to_datetime(f).date()
        except: pass
    if hasattr(f, 'date'):
        try: return f.date()
        except: pass
    return date.today()

def existe_historico_dia(fecha, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    d = _safe_to_date(fecha)
    inicio = datetime(d.year, d.month, d.day)
    fin = datetime(d.year, d.month, d.day, 23, 59, 59)
    return db.count("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}}) > 0

def obtener_historico_por_fecha(fecha, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    d = _safe_to_date(fecha)
    inicio = datetime(d.year, d.month, d.day); fin = datetime(d.year, d.month, d.day, 23, 59, 59)
    docs = db.find("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}}, limit=1)
    return docs[0] if docs else None

def borrar_historico_dia(fecha, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    d = _safe_to_date(fecha)
    inicio = datetime(d.year, d.month, d.day); fin = datetime(d.year, d.month, d.day, 23, 59, 59)
    db.delete("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}})

def fusionar_historico_dia(fecha, metricas_nuevas: dict, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    d = _safe_to_date(fecha)
    inicio = datetime(d.year, d.month, d.day); fin = datetime(d.year, d.month, d.day, 23, 59, 59)
    existente = db.find_one("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}})
    if existente:
        met_existente = existente.get("metricas", {})
        for clave, valor in metricas_nuevas.items():
            if isinstance(valor, dict):
                met_existente.setdefault(clave, {})
                for subclave, subvalor in valor.items():
                    try:
                        ant = float(met_existente[clave].get(subclave, 0))
                        nuev = float(subvalor)
                        res = ant + nuev
                        met_existente[clave][subclave] = int(res) if res.is_integer() else res
                    except (ValueError, TypeError):
                        pass
            else:
                try:
                    ant = float(met_existente.get(clave, 0))
                    nuev = float(valor)
                    res = ant + nuev
                    met_existente[clave] = int(res) if res.is_integer() else res
                except (ValueError, TypeError):
                    met_existente[clave] = valor
        db.update("historico", {"_id": existente["_id"]}, {"$set": {"metricas": met_existente, "fecha_carga": datetime.utcnow()}})
        return True
    return False

def registrar_auditoria(accion, modulo, detalle):
    db = get_db_v2()
    doc = {"timestamp": datetime.utcnow(), "usuario": st.session_state.get("username", "sistema"), "accion": accion, "modulo": modulo, "detalle": detalle}
    db.insert("auditoria", doc)


# ============================================================================
# ESTÁNDARES TEXTILES Y FACT_TRANSFERENCIAS ATÓMICAS (Centro de Control)
# ============================================================================
ESTANDARES_TEXTIL_DEFAULT = {
    'TEES': {'estandar_hora': 120, 'unidad': 'prendas/hora', 'nombre': 'Camisetas (Tees)'},
    'POLOS': {'estandar_hora': 100, 'unidad': 'prendas/hora', 'nombre': 'Polos'},
    'JEANS': {'estandar_hora': 75, 'unidad': 'prendas/hora', 'nombre': 'Jeans / Denim'},
    'PANTS': {'estandar_hora': 80, 'unidad': 'prendas/hora', 'nombre': 'Pantalones / Joggers'},
    'SHORTS': {'estandar_hora': 110, 'unidad': 'prendas/hora', 'nombre': 'Shorts'},
    'HOODIES': {'estandar_hora': 60, 'unidad': 'prendas/hora', 'nombre': 'Buzos / Hoodies'},
    'JACKETS': {'estandar_hora': 50, 'unidad': 'prendas/hora', 'nombre': 'Chaquetas / Coats'},
    'SWEATERS': {'estandar_hora': 70, 'unidad': 'prendas/hora', 'nombre': 'Suéteres'},
    'DRESSES': {'estandar_hora': 85, 'unidad': 'prendas/hora', 'nombre': 'Vestidos / Faldas'},
    'WOVENS': {'estandar_hora': 90, 'unidad': 'prendas/hora', 'nombre': 'Camisas (Wovens)'},
    'ACCESSORIES': {'estandar_hora': 150, 'unidad': 'prendas/hora', 'nombre': 'Accesorios / Mochilas'},
    'FUNDAS': {'estandar_hora': 300, 'unidad': 'fundas/hora', 'nombre': 'Fundas / Embalaje'},
    'OTROS': {'estandar_hora': 90, 'unidad': 'prendas/hora', 'nombre': 'General / Otros'}
}

def obtener_estandares_textiles() -> dict:
    """Obtiene los estándares de productividad parametrizables desde la base de datos o defaults."""
    db = get_db_v2()
    docs = db.find("config_estandares", {})
    if not docs:
        return ESTANDARES_TEXTIL_DEFAULT
    estandares = dict(ESTANDARES_TEXTIL_DEFAULT)
    for doc in docs:
        cat = doc.get("categoria", "").upper()
        if cat:
            estandares[cat] = {
                "estandar_hora": int(doc.get("estandar_hora", 90)),
                "unidad": doc.get("unidad", "prendas/hora"),
                "nombre": doc.get("nombre", cat)
            }
    return estandares

def guardar_estandar_textil(categoria: str, estandar_hora: int, unidad: str = "prendas/hora", nombre: str = None) -> bool:
    """Actualiza o inserta un estándar de productividad para una categoría textil."""
    db = get_db_v2()
    cat_upper = categoria.strip().upper()
    doc = {
        "categoria": cat_upper,
        "estandar_hora": int(estandar_hora),
        "unidad": unidad,
        "nombre": nombre or cat_upper,
        "actualizado_en": datetime.utcnow(),
        "usuario": st.session_state.get("username", "admin")
    }
    db.update("config_estandares", {"categoria": cat_upper}, doc, upsert=True)
    return True

def upsert_fact_transferencias(df_cruce: pd.DataFrame, fuente_origen: str = "EXCEL_HISTORICO", usuario: str = "admin") -> tuple[int, int]:
    """
    Inserta o actualiza registros atómicos en 'fact_transferencias' con hash único (mecanismo Upsert).
    Retorna (insertados, actualizados).
    """
    if df_cruce is None or df_cruce.empty:
        return 0, 0

    from core.data_auditor import DataAuditor
    db = get_db_v2()
    df_audit, errores = DataAuditor.auditar_dataset_transferencias(df_cruce)
    if df_audit.empty:
        return 0, 0

    insertados = 0
    actualizados = 0
    ahora = datetime.utcnow()

    for _, row in df_audit.iterrows():
        sec = str(row.get('SECUENCIAL', '')).strip()
        fecha_val = row.get('FECHA', None)
        f_date = _safe_to_date(fecha_val) or date.today()
        f_dt = datetime(f_date.year, f_date.month, f_date.day)
        
        tienda = str(row.get('TIENDA', '')).strip()
        transf = str(row.get('TRANSFERIDOR', 'Bodega Central')).strip()
        prendas = int(row.get('PRENDAS', row.get('CANTIDAD', 0)))
        fundas = int(row.get('FUNDAS', 0))
        costo = float(row.get('COSTO_TOTAL', row.get('COSTO', 0.0)))
        canton = str(row.get('CANTON', 'GENERAL')).strip()
        provincia = str(row.get('PROVINCIA', 'GENERAL')).strip()
        hash_reg = row.get('hash_registro', DataAuditor.generar_hash_transferencia(sec, f_date, tienda, transf))

        doc = {
            "hash_registro": hash_reg,
            "numero_transferencia": sec,
            "fecha_transferencia": f_dt,
            "fecha_str": f_date.strftime("%Y-%m-%d"),
            "anio": f_date.year,
            "mes": f_date.month,
            "semana_anio": int(f_date.strftime("%W")),
            "dia_semana": f_date.strftime("%A"),
            "transferidor": transf,
            "tienda": tienda,
            "canton": canton,
            "provincia": provincia,
            "prendas": prendas,
            "fundas": fundas,
            "total_unidades": prendas + fundas,
            "costo_total": costo,
            "fuente_origen": fuente_origen,
            "usuario_carga": usuario,
            "fecha_actualizacion": ahora
        }

        # Verificamos si ya existe para contabilizar inserción o actualización
        existente = db.find_one("fact_transferencias", {"hash_registro": hash_reg})
        if existente:
            db.update("fact_transferencias", {"hash_registro": hash_reg}, doc, upsert=True)
            actualizados += 1
        else:
            doc["fecha_creacion"] = ahora
            db.update("fact_transferencias", {"hash_registro": hash_reg}, doc, upsert=True)
            insertados += 1

    return insertados, actualizados

def consultar_fact_transferencias(fecha_inicio=None, fecha_fin=None, transferidor=None, tienda=None, provincia=None) -> pd.DataFrame:
    """
    Consulta transferencias atómicas indexadas desde 'fact_transferencias' con filtros multidimensionales.
    """
    db = get_db_v2()
    query = {}

    if fecha_inicio or fecha_fin:
        f_query = {}
        if fecha_inicio:
            d_ini = _safe_to_date(fecha_inicio)
            f_query["$gte"] = datetime(d_ini.year, d_ini.month, d_ini.day, 0, 0, 0)
        if fecha_fin:
            d_fin = _safe_to_date(fecha_fin)
            f_query["$lte"] = datetime(d_fin.year, d_fin.month, d_fin.day, 23, 59, 59)
        query["fecha_transferencia"] = f_query

    if transferidor and transferidor != "Todos los Transferidores":
        query["transferidor"] = transferidor
    if tienda and tienda != "Todas las Tiendas":
        query["tienda"] = tienda
    if provincia and provincia != "Todas las Provincias":
        query["provincia"] = provincia

    docs = db.find("fact_transferencias", query, sort=[("fecha_transferencia", DESCENDING)])
    if not docs:
        return pd.DataFrame()

    df = pd.DataFrame(docs)
    # Estandarizar nombres de columnas para interoperabilidad
    rename_dict = {
        'numero_transferencia': 'SECUENCIAL',
        'fecha_str': 'FECHA_STR',
        'transferidor': 'TRANSFERIDOR',
        'tienda': 'TIENDA',
        'canton': 'CANTON',
        'provincia': 'PROVINCIA',
        'prendas': 'PRENDAS',
        'fundas': 'FUNDAS',
        'total_unidades': 'CANTIDAD_TRANS',
        'costo_total': 'COSTO_TOTAL'
    }
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
    if 'fecha_transferencia' in df.columns:
        df['FECHA'] = pd.to_datetime(df['fecha_transferencia']).dt.date
    return df

