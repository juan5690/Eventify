from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UbicacionSchema(BaseModel):
    calle: str
    ciudad: str
    coordenadas: Optional[List[float]] = [-70.6506, -33.4372]
    capacidad: int = Field(..., ge=1)

class TicketSchema(BaseModel):
    tipo: str
    precio: float = Field(..., ge=0)
    stock_disponible: int = Field(..., ge=0)

class EventoCreate(BaseModel):
    titulo: str
    categoria: str
    fecha_evento: datetime
    ubicacion: UbicacionSchema
    tickets_disponibles: List[TicketSchema]

class EventoUpdate(BaseModel):
    titulo: Optional[str] = None
    categoria: Optional[str] = None
    fecha_evento: Optional[datetime] = None
    ubicacion: Optional[UbicacionSchema] = None
    tickets_disponibles: Optional[List[TicketSchema]] = None