import logging
from src.domain.entities.models import MovimientoInventario, GuiaRemision
from src.infrastructure.repositories.mongo_repository import MongoRepository
from src.application.decorators.audit import log_audit
from database.manager import local_db
from datetime import datetime

logger = logging.getLogger(__name__)

class LogisticService:
    def __init__(self):
        self.client = local_db.client
        self.db = local_db.db
        
        self.movimientos_repo = MongoRepository(self.db, "movimientos_inventario", MovimientoInventario)
        self.guias_repo = MongoRepository(self.db, "guias_remision", GuiaRemision)
        # Asumimos que el inventario se maneja por sku y cantidad en colección separada o dentro de inventario
        # Por simplicidad en este ejemplo, actualizamos 'inventario'

    @log_audit("registrar_despacho")
    def registrar_despacho(self, guia: GuiaRemision, usuario_responsable: str):
        """
        Registra un despacho (guía de remisión), resta stock y registra movimientos.
        Todo envuelto en una transacción de MongoDB para asegurar consistencia.
        """
        if not self.client:
            raise Exception("No hay conexión a la base de datos para iniciar la transacción.")

        with self.client.start_session() as session:
            with session.start_transaction():
                try:
                    # 1. Insertar la Guía de Remisión
                    self.guias_repo.insert(guia, session=session)
                    
                    # 2. Procesar cada item
                    for item in guia.items:
                        # Restar stock
                        result = self.db["inventario"].update_one(
                            {"sku": item.sku},
                            {"$inc": {"stock_actual": -item.cantidad}},
                            session=session
                        )
                        
                        if result.matched_count == 0:
                            # Si no existe, podemos decidir fallar la transacción
                            raise ValueError(f"SKU {item.sku} no encontrado en inventario.")
                        
                        # Crear movimiento
                        movimiento = MovimientoInventario(
                            sku=item.sku,
                            cantidad=-item.cantidad,
                            tipo_movimiento="EGRESO",
                            origen=guia.origen,
                            destino=guia.destino,
                            fecha=datetime.now(),
                            usuario_responsable=usuario_responsable
                        )
                        self.movimientos_repo.insert(movimiento, session=session)
                    
                    logger.info(f"Despacho {guia.numero_guia} registrado exitosamente.")
                    return True
                except Exception as e:
                    logger.error(f"Error en registrar_despacho, haciendo rollback: {e}")
                    raise
