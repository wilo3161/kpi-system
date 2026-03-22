# db_mongo.py
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import certifi
import json
import streamlit as st

class MongoDBConfig:
    """Configuración de MongoDB Atlas con soporte para Streamlit Secrets"""
    
    @staticmethod
    def get_mongo_uri():
        """Obtiene la URI de MongoDB desde Streamlit Secrets o variables de entorno"""
        try:
            # Primero intentar desde Streamlit Secrets (producción)
            return st.secrets["MONGO_URI"]
        except:
            # Fallback a variable de entorno (desarrollo local)
            return os.getenv("MONGO_URI", "")
    
    @staticmethod
    def get_db_name():
        """Obtiene el nombre de la base de datos"""
        try:
            return st.secrets["DATABASE_NAME"]
        except:
            return os.getenv("DATABASE_NAME", "aeropostale_erp")
    
    _client = None
    _db = None
    
    @classmethod
    def get_client(cls):
        """Obtiene el cliente MongoDB (singleton)"""
        if cls._client is None:
            mongo_uri = cls.get_mongo_uri()
            if not mongo_uri:
                raise ValueError("❌ MONGO_URI no está configurado. Configura en .streamlit/secrets.toml")
            
            try:
                cls._client = MongoClient(
                    mongo_uri,
                    tls=True,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=5000
                )
                # Verificar conexión
                cls._client.admin.command('ping')
                print("✅ Conexión exitosa a MongoDB Atlas")
            except ConnectionFailure as e:
                print(f"❌ Error de conexión a MongoDB: {e}")
                raise
        return cls._client
    
    @classmethod
    def get_db(cls):
        """Obtiene la base de datos"""
        if cls._db is None:
            client = cls.get_client()
            cls._db = client[cls.get_db_name()]
        return cls._db
    
    @classmethod
    def get_collection(cls, collection_name):
        """Obtiene una colección específica"""
        db = cls.get_db()
        return db[collection_name]


class MongoDatabase:
    """Capa de acceso a datos para MongoDB Atlas"""
    
    def __init__(self):
        self.collections = {}
        self._init_collections()
    
    def _init_collections(self):
        """Inicializa las colecciones necesarias"""
        collections_list = [
            'users', 'kpis', 'guias', 'trabajadores', 
            'gastos_procesados', 'logs_auditoria', 'distribuciones',
            'transferencias_detalle'
        ]
        
        for col_name in collections_list:
            self.collections[col_name] = MongoDBConfig.get_collection(col_name)
        
        # Crear índices para optimizar consultas
        self._create_indexes()
    
    def _create_indexes(self):
        """Crea índices para consultas frecuentes"""
        try:
            # Índices para kpis
            self.collections['kpis'].create_index('fecha', unique=True)
            
            # Índices para guias
            self.collections['guias'].create_index('numero', unique=True)
            self.collections['guias'].create_index('estado')
            
            # Índices para trabajadores
            self.collections['trabajadores'].create_index('area')
            self.collections['trabajadores'].create_index('estado')
            
            # Índices para logs
            self.collections['logs_auditoria'].create_index('usuario')
            self.collections['logs_auditoria'].create_index('created_at')
            
            print("✅ Índices creados exitosamente")
        except Exception as e:
            print(f"⚠️ Error creando índices (pueden ya existir): {e}")
    
    def _serialize_document(self, doc: Dict) -> Dict:
        """Convierte ObjectId a string para JSON/serialización"""
        if doc and '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc
    
    # ==================== OPERACIONES CRUD ====================
    
    def query(self, table: str, filters: Optional[Dict] = None, 
              limit: int = None, sort: tuple = None,
              projection: Dict = None) -> List[Dict]:
        """Consulta documentos en una colección"""
        try:
            collection = self.collections.get(table)
            if not collection:
                return []
            
            query = filters if filters else {}
            cursor = collection.find(query, projection)
            
            if sort:
                cursor = cursor.sort(sort[0], sort[1])
            if limit:
                cursor = cursor.limit(limit)
            
            return [self._serialize_document(doc) for doc in cursor]
            
        except Exception as e:
            print(f"Error en query: {e}")
            return []
    
    def query_one(self, table: str, filters: Dict) -> Optional[Dict]:
        """Consulta un solo documento"""
        try:
            collection = self.collections.get(table)
            if not collection:
                return None
            
            doc = collection.find_one(filters)
            return self._serialize_document(doc) if doc else None
            
        except Exception as e:
            print(f"Error en query_one: {e}")
            return None
    
    def insert(self, table: str, data: Union[Dict, List]) -> bool:
        """Inserta uno o varios documentos"""
        try:
            collection = self.collections.get(table)
            if not collection:
                return False
            
            now = datetime.now()
            
            if isinstance(data, dict):
                data['created_at'] = now
                data['updated_at'] = now
                result = collection.insert_one(data)
                return result.acknowledged
                
            elif isinstance(data, list):
                for doc in data:
                    doc['created_at'] = now
                    doc['updated_at'] = now
                result = collection.insert_many(data)
                return result.acknowledged
            
            return False
            
        except DuplicateKeyError as e:
            print(f"Error: Documento duplicado - {e}")
            return False
        except Exception as e:
            print(f"Error en insert: {e}")
            return False
    
    def update(self, table: str, id: Union[str, Any], data: Dict, id_field: str = "_id") -> bool:
        """Actualiza un documento por ID"""
        try:
            collection = self.collections.get(table)
            if not collection:
                return False
            
            data['updated_at'] = datetime.now()
            
            if id_field == "_id" and isinstance(id, str):
                from bson import ObjectId
                filter_query = {"_id": ObjectId(id)}
            else:
                filter_query = {id_field: id}
            
            result = collection.update_one(filter_query, {'$set': data})
            return result.modified_count > 0
            
        except Exception as e:
            print(f"Error en update: {e}")
            return False
    
    def delete(self, table: str, id: Union[str, Any], id_field: str = "_id") -> bool:
        """Elimina un documento por ID"""
        try:
            collection = self.collections.get(table)
            if not collection:
                return False
            
            if id_field == "_id" and isinstance(id, str):
                from bson import ObjectId
                filter_query = {"_id": ObjectId(id)}
            else:
                filter_query = {id_field: id}
            
            result = collection.delete_one(filter_query)
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"Error en delete: {e}")
            return False
    
    def count(self, table: str, filters: Optional[Dict] = None) -> int:
        """Cuenta documentos en una colección"""
        try:
            collection = self.collections.get(table)
            if not collection:
                return 0
            
            query = filters if filters else {}
            return collection.count_documents(query)
            
        except Exception as e:
            print(f"Error en count: {e}")
            return 0
    
    def get_as_dataframe(self, table: str, filters: Optional[Dict] = None) -> pd.DataFrame:
        """Obtiene documentos como DataFrame de pandas"""
        docs = self.query(table, filters)
        if docs:
            return pd.DataFrame(docs)
        return pd.DataFrame()
    
    def insert_many(self, table: str, data: List[Dict]) -> bool:
        """Inserta múltiples documentos"""
        return self.insert(table, data)
    
    def log_action(self, usuario: str, modulo: str, accion: str, 
                   detalles: Dict = None, ip: str = None) -> bool:
        """Registra una acción en el log de auditoría"""
        try:
            log_data = {
                'usuario': usuario,
                'modulo': modulo,
                'accion': accion,
                'detalles': json.dumps(detalles, default=str) if detalles else None,
                'ip_address': ip,
                'created_at': datetime.now()
            }
            return self.insert('logs_auditoria', log_data)
            
        except Exception as e:
            print(f"Error en log_action: {e}")
            return False


# Instancia global para usar en toda la aplicación
db = MongoDatabase()