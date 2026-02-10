"""
Base de datos local simulada para el sistema ERP
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from .helpers import hash_password


class LocalDatabase:
    """
    Simulación de base de datos local para el sistema ERP
    """
    
    def __init__(self):
        self.data = {
            'users': [
                {'id': 1, 'username': 'admin', 'role': 'admin', 'password_hash': hash_password('admin123')},
                {'id': 2, 'username': 'user', 'role': 'user', 'password_hash': hash_password('user123')},
                {'id': 3, 'username': 'wilson', 'role': 'admin', 'password_hash': hash_password('admin123')}
            ],
            'kpis': self._generate_kpis_data(),
            'guias': [],
            'trabajadores': [],
            'distribuciones': [
                {'id': 1, 'transporte': 'Tempo', 'guías': 45, 'estado': 'En ruta'},
                {'id': 2, 'transporte': 'Luis Perugachi', 'guías': 32, 'estado': 'Entregado'}
            ]
        }
    
    def _generate_kpis_data(self):
        """Genera datos de KPIs de demostración"""
        kpis = []
        today = datetime.now()
        for i in range(30):
            date = today - timedelta(days=i)
            kpis.append({
                'id': i,
                'fecha': date.strftime('%Y-%m-%d'),
                'produccion': np.random.randint(800, 1500),
                'eficiencia': np.random.uniform(85, 98),
                'alertas': np.random.randint(0, 5),
                'costos': np.random.uniform(5000, 15000)
            })
        return kpis
    
    def query(self, table: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Consulta datos de una tabla
        
        Args:
            table: Nombre de la tabla
            filters: Filtros opcionales (dict con key-value)
            
        Returns:
            Lista de registros que coinciden con los filtros
        """
        if table not in self.data:
            return []
        
        results = self.data[table]
        if filters:
            for key, value in filters.items():
                results = [item for item in results if item.get(key) == value]
        return results
    
    def insert(self, table: str, data: Any) -> bool:
        """
        Inserta datos en una tabla
        
        Args:
            table: Nombre de la tabla
            data: Dict o lista de dicts a insertar
            
        Returns:
            True si la inserción fue exitosa
        """
        if table not in self.data:
            self.data[table] = []
        
        if isinstance(data, dict):
            data['id'] = len(self.data[table]) + 1
            self.data[table].append(data)
        elif isinstance(data, list):
            for item in data:
                item['id'] = len(self.data[table]) + 1
                self.data[table].append(item)
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Autentica un usuario
        
        Args:
            username: Nombre de usuario
            password: Contraseña en texto plano
            
        Returns:
            Dict con datos del usuario si la autenticación es exitosa, None en caso contrario
        """
        users = self.query('users', {'username': username})
        if not users:
            return None
        
        user = users[0]
        if user['password_hash'] == hash_password(password):
            return user
        return None
