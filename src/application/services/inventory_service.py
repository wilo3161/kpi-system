import logging
from src.domain.entities.models import Producto
from src.infrastructure.repositories.mongo_repository import MongoRepository
from src.application.decorators.audit import log_audit
from database.manager import local_db

logger = logging.getLogger(__name__)

class InventoryService:
    def __init__(self):
        self.client = local_db.client
        self.db = local_db.db
        self.productos_repo = MongoRepository(self.db, "inventario", Producto)

    @log_audit("crear_producto")
    def crear_producto(self, producto: Producto, usuario_responsable: str):
        # Validate existence
        existente = self.productos_repo.find_one({"sku": producto.sku})
        if existente:
            raise ValueError(f"El producto con SKU {producto.sku} ya existe.")
        
        return self.productos_repo.insert(producto)
    
    @log_audit("calcular_rop")
    def calcular_rop(self, sku: str, lead_time_dias: int, ventas_historicas_30dias: int) -> float:
        """
        Calcula el Reorder Point (ROP).
        Fórmula básica: (Demanda Promedio Diaria * Lead Time)
        """
        demanda_diaria = ventas_historicas_30dias / 30.0
        rop = demanda_diaria * lead_time_dias
        logger.info(f"ROP calculado para {sku}: {rop}")
        return rop
