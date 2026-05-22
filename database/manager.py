import streamlit as st
import os
import random
import pandas as pd
from datetime import datetime, timedelta, date
from pymongo import MongoClient, ReturnDocument
from utils.common import hash_password

try:
    from pydantic import BaseModel, ValidationError, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

from typing import Optional, Dict, Any

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
        stripped = doc.strip()
        if stripped:
            try: return int(stripped)
            except ValueError:
                try: return float(stripped)
                except ValueError: return doc
        return doc
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
            return {k: int(float(val)) for k, val in v.items()}

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
    COLLECTIONS = ["users", "kpis", "historico", "guias", "transferencias", "inventario", "correos", "telegram_log", "whatsapp_log", "reconciliacion", "ml_predictions", "notificaciones", "auditoria", "config", "equipo_logistico", "secuencia_guias", "kpi_analytics", "manifiesto"]
    def __init__(self):
        self.connected = False; self.client = None; self.db = None; self._connect()
    def _connect(self):
        try:
            uri = None; db_name = "aeropostale_erp"
            for secret_key in ["mongo", "mongodb"]:
                try: uri = st.secrets[secret_key]["URI"]; db_name = st.secrets[secret_key].get("DB_NAME", db_name); break
                except (KeyError, AttributeError): pass
            if not uri: uri = os.environ.get("MONGODB_URI")
            if not uri: raise ValueError("No se encontró cadena de conexión MongoDB.")
            self.client = MongoClient(uri, serverSelectionTimeoutMS=6000)
            self.client.server_info()
            self.db = self.client[db_name]; self.connected = True
            self._seed_if_empty(); self._ensure_required_users()
        except Exception as e:
            self.connected = False; self._connection_error = str(e)
    def _seed_if_empty(self):
        try:
            if self.db["equipo_logistico"].count_documents({}) == 0:
                equipo_inicial = [{"nombre": "Wilson Pérez", "cargo": "Jefe de Logística / CD", "area": "Liderazgo", "email": "wperez@fashionclub.com.ec", "whatsapp": "0993052744", "telegram": "0993052744"}, {"nombre": "Andrés Yépez", "cargo": "Transferencias Fashion", "area": "Transferencias", "email": "cyepez@fashionclub.com.ec", "whatsapp": "0995529505", "telegram": "0995529505"}, {"nombre": "Luis Perugachi", "cargo": "Pivote Transferencias", "area": "Transferencias", "email": "lperugachi@fashionclub.com.ec", "whatsapp": "0993012238", "telegram": "0993012238"}, {"nombre": "Josué Imbacúan", "cargo": "Transferencias Tempo", "area": "Transferencias", "email": "jimbacuan@fashionclub.com.ec", "whatsapp": "0988856682", "telegram": "0988856682"}, {"nombre": "Jessica Suárez", "cargo": "Distribución", "area": "Distribución", "email": "jsuarez@fashionclub.com.ec", "whatsapp": "0981951052", "telegram": "0981951052"}, {"nombre": "Jhonny Villa", "cargo": "Empaque y Gestión Guías", "area": "Empaque", "email": "jvilla@fashionclub.com.ec", "whatsapp": "0968491147", "telegram": "0968491147"}, {"nombre": "Simón Vera", "cargo": "Apoyo Guías y Envíos", "area": "Empaque", "email": "bodega@fashionclub.com.ec", "whatsapp": "0969341528", "telegram": "0969341528"}, {"nombre": "Jhonny Guadalupe", "cargo": "Ventas al Por Mayor", "area": "Ventas Mayoristas", "email": "jguadalupe@fashionclub.com.ec", "whatsapp": "0985603835", "telegram": "0985603835"}, {"nombre": "Rocío Cadena", "cargo": "Ventas al Por Mayor", "area": "Ventas Mayoristas", "email": "jcadena@fashionclub.com.ec", "whatsapp": "0992062862", "telegram": "0992062862"}, {"nombre": "Diana García", "cargo": "Reprocesado Prendas", "area": "Cuarentena", "email": "dgarcia@fashionclub.com.ec", "whatsapp": "0980837688", "telegram": "0980837688"}]
                self.db["equipo_logistico"].insert_many(equipo_inicial)
        except: pass
    def _ensure_required_users(self):
        required_users = [{"username": "admin", "password": hash_password("wilo3161"), "role": "Administrador", "name": "Wilson Pérez", "email": "wperez@fashionclub.com.ec"}, {"username": "logistica", "password": hash_password("log123"), "role": "Logística", "name": "Coordinador Logístico", "email": ""}, {"username": "ventas", "password": hash_password("ven123"), "role": "Ventas", "name": "Ejecutivo de Ventas", "email": ""}, {"username": "Andres", "password": hash_password("Andres145"), "role": "Bodega", "name": "Andrés Yépez", "email": "cyepez@fashionclub.com.ec"}, {"username": "Luis", "password": hash_password("luis230499"), "role": "Bodega", "name": "Luis Perugachi", "email": "lperugachi@fashionclub.com.ec"}, {"username": "Jessica", "password": hash_password("bod123"), "role": "Bodega", "name": "Jessica Suárez", "email": "jsuarez@fashionclub.com.ec"}, {"username": "Josue", "password": hash_password("bod123"), "role": "Bodega", "name": "Josué Imbacúan", "email": "jimbacuan@fashionclub.com.ec"}]
        try:
            from pymongo import InsertOne, DeleteMany
            existing = {u["username"] for u in self.db["users"].find({}, {"username": 1})}
            new_users = []
            for u in required_users:
                if u["username"] not in existing:
                    u_copy = u.copy()
                    u_copy["_created"] = datetime.utcnow()
                    new_users.append(u_copy)
            if new_users:
                self.db["users"].bulk_write([InsertOne(u) for u in new_users])
        except:
            # Fallback: insert uno por uno
            for user in required_users:
                try:
                    if not self.find_one("users", {"username": user["username"]}):
                        user["_created"] = datetime.utcnow()
                        self.insert("users", user)
                except:
                    pass
    def _validate_historico(self, doc):
        if not PYDANTIC_AVAILABLE or HistoricoModel is None: return doc
        try: validated = HistoricoModel(**doc); return validated.model_dump()
        except ValidationError: return doc
    def insert(self, collection, doc, session=None):
        if not self.connected: return
        if collection == "historico": doc = self._validate_historico(doc)
        doc["_created"] = datetime.utcnow()
        return self.db[collection].insert_one(doc, session=session).inserted_id
    def find(self, collection, query={}, sort=None, limit=0, session=None):
        if not self.connected: return []
        cursor = self.db[collection].find(query, session=session)
        if sort: cursor = cursor.sort(sort)
        if limit: cursor = cursor.limit(limit)
        docs = [_sanitize_document(doc) for doc in cursor]
        if collection == "historico": docs = [self._validate_historico(d) for d in docs]
        return docs
    def find_one(self, collection, query, session=None):
        if not self.connected: return None
        doc = self.db[collection].find_one(query, session=session)
        if doc:
            doc = _sanitize_document(doc)
            if collection == "historico": doc = self._validate_historico(doc)
        return doc
    def find_one_and_update(self, collection, filter, update, upsert=False, session=None):
        if not self.connected: return None
        doc = self.db[collection].find_one_and_update(filter, update, upsert=upsert, return_document=ReturnDocument.AFTER, session=session)
        if doc:
            doc = _sanitize_document(doc)
            if collection == "historico": doc = self._validate_historico(doc)
        return doc
    def update(self, collection, query, update_doc, upsert=False, session=None):
        if not self.connected: return
        if any(k.startswith("$") for k in update_doc.keys()): self.db[collection].update_one(query, update_doc, upsert=upsert, session=session)
        else: self.db[collection].update_one(query, {"$set": update_doc}, upsert=upsert, session=session)
    def delete(self, collection, query, session=None):
        if not self.connected: return
        self.db[collection].delete_many(query, session=session)
    def count(self, collection, query={}):
        if not self.connected: return 0
        return self.db[collection].count_documents(query)
    def authenticate(self, username, password_hash): return self.find_one("users", {"username": username, "password": password_hash})
    def update_password(self, username, new_hash): self.update("users", {"username": username}, {"password": new_hash}); return True
    def guardar_config(self, clave, valor): self.update("config", {"clave": clave}, {"valor": valor}, upsert=True)
    def leer_config(self, clave, default=None): doc = self.find_one("config", {"clave": clave}); return doc["valor"] if doc else default

class MockLocalDBFallback:
    def __init__(self): # CORREGIDO: __init__
        self.connected = False; self._fallback_data = {c: [] for c in MongoDBAtlas.COLLECTIONS}; self._connection_error = ""
    def _get_data(self):
        try:
            if "mock_db" not in st.session_state: st.session_state.mock_db = self._fallback_data
            return st.session_state.mock_db
        except: return self._fallback_data
    def _ensure_mock_data(self):
        data = self._get_data()
        if not data.get("users"): data["users"] = [{"username": "admin", "password": hash_password("wilo3161"), "role": "Administrador", "name": "Administrador General"}, {"username": "logistica", "password": hash_password("log123"), "role": "Logística", "name": "Coordinador Logístico"}, {"username": "ventas", "password": hash_password("ven123"), "role": "Ventas", "name": "Ejecutivo de Ventas"}, {"username": "Andres", "password": hash_password("Andres145"), "role": "Bodega", "name": "Andrés Yépez"}, {"username": "Luis", "password": hash_password("luis230499"), "role": "Bodega", "name": "Luis Perugachi"}, {"username": "Jessica", "password": hash_password("bod123"), "role": "Bodega", "name": "Jessica Suárez"}, {"username": "Josue", "password": hash_password("bod123"), "role": "Bodega", "name": "Josué Imbacúan"}]
        if not data.get("kpis"): data["kpis"] = [{"fecha": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "unidades": random.randint(800, 1500), "tiendas": random.randint(35, 42)} for i in range(30)]
        if not data.get("equipo_logistico"): data["equipo_logistico"] = [{"nombre": "Wilson Pérez", "cargo": "Jefe", "area": "Liderazgo", "whatsapp": "0993052744", "email": "wperez@fashionclub.com.ec"}, {"nombre": "Andrés Yépez", "cargo": "Transferencias", "area": "Transferencias", "whatsapp": "0995529505", "email": "cyepez@fashionclub.com.ec"}]
    def _validate_historico(self, doc):
        if not PYDANTIC_AVAILABLE or HistoricoModel is None: return doc
        try: validated = HistoricoModel(**doc); return validated.model_dump()
        except ValidationError: return doc
    def insert(self, collection, doc, session=None):
        self._ensure_mock_data(); data = self._get_data()
        if collection == "historico": doc = self._validate_historico(doc)
        doc["_created"] = datetime.utcnow()
        if collection not in data: data[collection] = []
        data[collection].append(doc)
    def find(self, collection, query={}, sort=None, limit=0, session=None):
        self._ensure_mock_data(); data = self._get_data()
        results = [d for d in data.get(collection, []) if all(d.get(k) == v for k, v in query.items())]
        if sort:
            for s in sort:
                key, direction = s if isinstance(s, tuple) else (s, 1)
                results.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
        if limit: results = results[:limit]
        sanitized = [_sanitize_document(doc) for doc in results]
        if collection == "historico": sanitized = [self._validate_historico(d) for d in sanitized]
        return sanitized
    def find_one(self, collection, query, session=None):
        self._ensure_mock_data(); data = self._get_data()
        for d in data.get(collection, []):
            if all(d.get(k) == v for k, v in query.items()):
                doc = _sanitize_document(d)
                if collection == "historico": return self._validate_historico(doc)
                return doc
        return None
    def find_one_and_update(self, collection, filter, update, upsert=False, session=None):
        doc = self.find_one(collection, filter)
        if doc:
            for key, inc_val in update.get("$inc", {}).items(): doc[key] = doc.get(key, 0) + inc_val
            return doc
        elif upsert:
            new_doc = filter.copy(); new_doc["secuencia"] = 1; self.insert(collection, new_doc); return new_doc
        return None
    def update(self, collection, query, update_doc, upsert=False, session=None):
        self._ensure_mock_data(); doc = self.find_one(collection, query)
        if doc:
            if any(k.startswith("$") for k in update_doc.keys()):
                for op, fields in update_doc.items():
                    if op == "$set": doc.update(fields)
                    elif op == "$inc":
                        for f, inc in fields.items(): doc[f] = doc.get(f, 0) + inc
            else: doc.update(update_doc)
        elif upsert:
            new_doc = query.copy()
            if any(k.startswith("$") for k in update_doc.keys()):
                if "$set" in update_doc: new_doc.update(update_doc["$set"])
            else: new_doc.update(update_doc)
            self.insert(collection, new_doc)
    def delete(self, collection, query, session=None):
        self._ensure_mock_data(); data = self._get_data()
        data[collection] = [d for d in data.get(collection, []) if not all(d.get(k) == v for k, v in query.items())]
    def count(self, collection, query={}): return len(self.find(collection, query))
    def authenticate(self, username, password_hash): return self.find_one("users", {"username": username, "password": password_hash})
    def update_password(self, username, new_hash):
        doc = self.find_one("users", {"username": username})
        if doc: doc["password"] = new_hash; return True
        return False
    def guardar_config(self, clave, valor): self.update("config", {"clave": clave}, {"valor": valor}, upsert=True)
    def leer_config(self, clave, default=None): doc = self.find_one("config", {"clave": clave}); return doc["valor"] if doc else default

def get_db_v2():
    try:
        mongo_db = MongoDBAtlas()
        if mongo_db.connected: return mongo_db
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
        if datos_df is not None and not datos_df.empty: resumen = datos_df.describe(include='all').to_dict()
    except: pass
    doc = {"modulo": modulo, "pestaña": pestaña, "archivo_nombre": archivo_nombre, "fecha_archivo": fecha_archivo_dt, "fecha_carga": datetime.utcnow(), "usuario": usuario, "metricas": metricas_limpias, "resumen_df": resumen, "filas": len(datos_df) if datos_df is not None else 0, "columnas": len(datos_df.columns) if datos_df is not None and not datos_df.empty else 0}
    db.insert("historico", doc)

def consultar_historico(modulo, pestaña=None, fecha_desde=None, fecha_hasta=None, usuario=None):
    db = get_db_v2()
    query = {"modulo": modulo}
    if pestaña and pestaña not in ("Todas", "Todos", ""): query["pestaña"] = pestaña
    fecha_desde_dt = _safe_to_datetime(fecha_desde); fecha_hasta_dt = _safe_to_datetime(fecha_hasta)
    if fecha_desde_dt or fecha_hasta_dt:
        fecha_query = {}
        if fecha_desde_dt: fecha_query["$gte"] = fecha_desde_dt
        if fecha_hasta_dt: fecha_query["$lte"] = datetime(fecha_hasta_dt.year, fecha_hasta_dt.month, fecha_hasta_dt.day, 23, 59, 59)
        query["fecha_archivo"] = fecha_query
    if usuario: query["usuario"] = usuario
    return db.find("historico", query, sort=[("fecha_archivo", -1)])

def existe_historico_dia(fecha: date, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    inicio = datetime(fecha.year, fecha.month, fecha.day)
    fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    return len(db.find("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}})) > 0

def obtener_historico_por_fecha(fecha: date, pestaña="Transferencias Diarias"):
    db = get_db_v2()
    inicio = datetime(fecha.year, fecha.month, fecha.day); fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    docs = db.find("historico", {"modulo": "dashboard_logistico", "pestaña": pestaña, "fecha_archivo": {"$gte": inicio, "$lte": fin}})
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

def guardar_operacion_logistica(data: dict) -> bool:
    """
    Valida e inserta una operación logística en la colección 'historico' (como modulo 'dashboard_logistico')
    con soporte transaccional ACID si la base de datos es real.
    """
    # 1. Validar campos obligatorios
    campos_obligatorios = ["fecha", "tipo_operacion", "cantidad", "responsable"]
    for campo in campos_obligatorios:
        if campo not in data or data[campo] is None:
            return False
            
    # Validar tipos
    fecha_val = _safe_to_datetime(data["fecha"])
    if not fecha_val:
        return False
        
    tipo_op = str(data["tipo_operacion"]).strip()
    if not tipo_op:
        return False
        
    try:
        cant_val = float(data["cantidad"])
        if cant_val < 0:
            return False
    except (ValueError, TypeError):
        return False
        
    resp = str(data["responsable"]).strip()
    if not resp:
        return False
        
    # Obtener la instancia de DB activa
    db = get_db_v2()
    if isinstance(db, MongoDBAtlas) and not db.connected:
        return False
        
    # Si no es cliente MongoDB Atlas real (es MockLocalDBFallback), guardar directamente
    if not hasattr(db, "client") or db.client is None:
        try:
            doc = {
                "modulo": "dashboard_logistico",
                "pestaña": tipo_op,
                "archivo_nombre": data.get("archivo_nombre", "manual"),
                "fecha_archivo": fecha_val,
                "fecha_carga": datetime.utcnow(),
                "usuario": resp,
                "metricas": {
                    "total_unidades": int(cant_val),
                    "por_categoria": data.get("por_categoria", {})
                },
                "filas": 1,
                "columnas": 2
            }
            db.insert("historico", doc)
            return True
        except Exception:
            return False
            
    # Si es MongoDB Atlas con cliente real, usar transacciones con try-except
    session = None
    try:
        session = db.client.start_session()
        session.start_transaction()
        
        doc = {
            "modulo": "dashboard_logistico",
            "pestaña": tipo_op,
            "archivo_nombre": data.get("archivo_nombre", "manual"),
            "fecha_archivo": fecha_val,
            "fecha_carga": datetime.utcnow(),
            "usuario": resp,
            "metricas": {
                "total_unidades": int(cant_val),
                "por_categoria": data.get("por_categoria", {})
            },
            "filas": 1,
            "columnas": 2
        }
        db.insert("historico", doc, session=session)
        
        session.commit_transaction()
        return True
    except Exception as e:
        if session:
            try:
                session.abort_transaction()
            except:
                pass
        return False
    finally:
        if session:
            session.end_session()
