from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class Producto(BaseModel):
    sku: str = Field(..., title="SKU del Producto")
    nombre: str = Field(..., title="Nombre descriptivo")
    stock_actual: int = Field(default=0, ge=0, title="Stock físico actual")
    categoria: Optional[str] = None
    precio: Optional[float] = Field(default=0.0, ge=0.0)

class MovimientoInventario(BaseModel):
    sku: str
    cantidad: int = Field(..., description="Cantidad movida. Positiva para ingresos, negativa para egresos.")
    tipo_movimiento: str = Field(..., pattern="^(INGRESO|EGRESO|AJUSTE|TRASLADO)$")
    origen: Optional[str] = None
    destino: Optional[str] = None
    fecha: datetime = Field(default_factory=datetime.now)
    usuario_responsable: str

class Empleado(BaseModel):
    nombre: str
    area: str
    cargo: str
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    telegram_id: Optional[str] = None

class GuiaItem(BaseModel):
    sku: str
    cantidad: int = Field(..., gt=0)

class GuiaRemision(BaseModel):
    numero_guia: str
    fecha_emision: datetime = Field(default_factory=datetime.now)
    origen: str
    destino: str
    transportista: str
    placa_vehiculo: Optional[str] = None
    items: List[GuiaItem]
    estado: str = Field(default="EMITIDA", pattern="^(EMITIDA|EN_TRANSITO|ENTREGADA|ANULADA)$")
