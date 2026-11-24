from fastapi import APIRouter, HTTPException
from backend.models.schemas import EventoCreate, EventoUpdate
from backend.services import eventos_service

router = APIRouter(prefix="/api/v1/eventos", tags=["Gestión Operativa (CRUD)"])

@router.get("/")
def get_eventos():
    return eventos_service.listar_eventos()

@router.get("/{evento_id}")
def get_evento(evento_id: str):
    evento = eventos_service.obtener_evento(evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return evento

@router.post("/", status_code=201)
def post_evento(evento: EventoCreate):
    return eventos_service.crear_evento(evento)

@router.put("/{evento_id}")
def put_evento(evento_id: str, evento: EventoUpdate):
    actualizado = eventos_service.actualizar_evento(evento_id, evento)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return actualizado

@router.delete("/{evento_id}")
def delete_evento(evento_id: str):
    if not eventos_service.eliminar_evento(evento_id):
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return {"mensaje": "Evento eliminado correctamente"}