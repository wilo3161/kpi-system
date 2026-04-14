# config/mongodb.py
"""
Configuración de conexión a MongoDB Atlas
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import streamlit as st
from datetime import datetime
import os

def get_mongo_client():
    """Obtiene cliente MongoDB desde secrets o variables de entorno"""
    try:
        # Opción 1: Streamlit Secrets (recomendado para producción)
        if "mongodb" in st.secrets:
            uri = st.secrets["mongodb"]["uri"]
            return MongoClient(uri, server_api=ServerApi('1'))
    except Exception as e:
        print(f"No se pudo cargar desde secrets: {e}")
    
    # Opción 2: Variables de entorno
    uri = os.getenv("MONGODB_URI")
    if uri:
        return MongoClient(uri, server_api=ServerApi('1'))
    
    return None

def get_database():
    """Obtiene la base de datos de MongoDB"""
    client = get_mongo_client()
    if client is None:
        return None
    
    try:
        db_name = st.secrets.get("mongodb", {}).get("database", "aeropostale_erp")
    except:
        db_name = os.getenv("MONGODB_DATABASE", "aeropostale_erp")
    
    return client[db_name]

class MongoDB:
    """
    Clase que reemplaza MockLocalDB para usar MongoDB Atlas
    Mantiene la misma interfaz para no romper el código existente
    """
    
    def __init__(self):
        self.db = get_database()
        self.client = get_mongo_client()
        self._fallback = None  # Referencia a MockLocalDB si es necesario
        
    def _get_collection(self, table_name):
        """Obtiene una colección de MongoDB"""
        if self.db is None:
            return None
        return self.db[table_name]
    
    def query(self, table_name, filters=None):
        """Consulta documentos en una colección"""
        collection = self._get_collection(table_name)
        if collection is None:
            return []
        
        try:
            if filters:
                cursor = collection.find(filters)
            else:
                cursor = collection.find()
            
            results = []
            for doc in cursor:
                doc['id'] = str(doc.pop('_id'))
                results.append(doc)
            return results
            
        except Exception as e:
            print(f"Error en query '{table_name}': {e}")
            return []
    
    def insert(self, table_name, data):
        """Inserta un documento o lista de documentos"""
        collection = self._get_collection(table_name)
        if collection is None:
            return False
        
        try:
            timestamp = datetime.now().isoformat()
            
            if isinstance(data, dict):
                data['created_at'] = timestamp
                data['updated_at'] = timestamp
                result = collection.insert_one(data)
                return str(result.inserted_id)
                
            elif isinstance(data, list):
                for item in data:
                    item['created_at'] = timestamp
                    item['updated_at'] = timestamp
                result = collection.insert_many(data)
                return [str(id) for id in result.inserted_ids]
                
            return False
            
        except Exception as e:
            print(f"Error en insert '{table_name}': {e}")
            return False
    
    def delete(self, table_name, id):
        """Elimina un documento por su ID"""
        collection = self._get_collection(table_name)
        if collection is None:
            return False
        
        try:
            from bson.objectid import ObjectId
            
            try:
                result = collection.delete_one({'_id': ObjectId(id)})
                if result.deleted_count > 0:
                    return True
            except:
                pass
            
            result = collection.delete_one({'id': id})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error en delete '{table_name}': {e}")
            return False
    
    def update(self, table_name, id, update_data):
        """Actualiza un documento por su ID"""
        collection = self._get_collection(table_name)
        if collection is None:
            return False
        
        try:
            from bson.objectid import ObjectId
            
            update_data['updated_at'] = datetime.now().isoformat()
            
            try:
                result = collection.update_one(
                    {'_id': ObjectId(id)},
                    {'$set': update_data}
                )
                if result.matched_count > 0:
                    return True
            except:
                pass
            
            result = collection.update_one(
                {'id': id},
                {'$set': update_data}
            )
            return result.matched_count > 0
            
        except Exception as e:
            print(f"Error en update '{table_name}': {e}")
            return False
    
    def authenticate(self, username, password):
        """Autenticación de usuarios"""
        users = self.query("users", {"username": username})
        if not users:
            return None
        
        user = users[0]
        import hashlib
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user.get("password_hash") == input_hash:
            return user
        return None

def inicializar_datos_base():
    """Inicializa datos base en MongoDB si las colecciones están vacías"""
    db = get_database()
    if db is None:
        print("❌ No hay conexión a MongoDB")
        return False
    
    import numpy as np
    from datetime import timedelta
    
    # 1. Usuarios base
    if db.users.count_documents({}) == 0:
        usuarios_base = [
            {
                "username": "admin",
                "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
                "role": "Administrador",
                "name": "Administrador General",
                "email": "admin@aeropostale.com",
                "avatar": "👑",
                "created_at": datetime.now().isoformat()
            },
            {
                "username": "logistica",
                "password_hash": "ac9689e2272427085e35b9d3e3e8bed881dc0875238cc8b943d0c0a2dab71e2f",
                "role": "Logística",
                "name": "Coordinador Logístico",
                "email": "logistica@aeropostale.com",
                "avatar": "🚚",
                "created_at": datetime.now().isoformat()
            },
            {
                "username": "ventas",
                "password_hash": "f5bb8c3f6a6e2e6b8a3c8f8e8d8c8b8a7f6e5d4c3b2a19080706050403020100",
                "role": "Ventas",
                "name": "Ejecutivo de Ventas",
                "email": "ventas@aeropostale.com",
                "avatar": "💼",
                "created_at": datetime.now().isoformat()
            },
            {
                "username": "bodega",
                "password_hash": "a8f5f167f44f4964e6c998dee827110c9a0c5e1e7a5b6e8f9c0d1e2f3a4b5c6d",
                "role": "Bodega",
                "name": "Supervisor de Bodega",
                "email": "bodega@aeropostale.com",
                "avatar": "📦",
                "created_at": datetime.now().isoformat()
            }
        ]
        db.users.insert_many(usuarios_base)
        print("✅ Usuarios base creados")
    
    # 2. KPIs de ejemplo
    if db.kpis.count_documents({}) == 0:
        kpis = []
        today = datetime.now()
        for i in range(30):
            date = today - timedelta(days=i)
            kpis.append({
                "fecha": date.strftime("%Y-%m-%d"),
                "produccion": int(np.random.randint(800, 1500)),
                "eficiencia": float(np.random.uniform(85, 98)),
                "alertas": int(np.random.randint(0, 5)),
                "costos": float(np.random.uniform(5000, 15000)),
                "created_at": datetime.now().isoformat()
            })
        db.kpis.insert_many(kpis)
        print("✅ KPIs de ejemplo creados")
    
    # 3. Trabajadores base
    if db.trabajadores.count_documents({}) == 0:
        trabajadores_base = [
            {"nombre": "Andres Yepez", "cargo": "Supervisor", "estado": "Activo", "es_base": True, "area": "Liderazgo y Control"},
            {"nombre": "Josue Imbacuan", "cargo": "Operador", "estado": "Activo", "es_base": True, "area": "Gestion de Transferencias"},
            {"nombre": "Maria Gonzalez", "cargo": "Auditora", "estado": "Activo", "es_base": True, "area": "Reproceso y Calidad"}
        ]
        db.trabajadores.insert_many(trabajadores_base)
        print("✅ Trabajadores base creados")
    
    return True