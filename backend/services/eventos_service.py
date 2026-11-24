from bson import ObjectId
from backend.database import get_db
from backend.models.schemas import EventoCreate, EventoUpdate

db = get_db()
coleccion = db["eventos"]

def serializar_evento(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    if "fecha_evento" in doc and hasattr(doc["fecha_evento"], "isoformat"):
        doc["fecha_evento"] = doc["fecha_evento"].isoformat()
    return doc

def listar_eventos():
    return [serializar_evento(doc) for doc in coleccion.find()]

def obtener_evento(evento_id: str):
    doc = coleccion.find_one({"_id": ObjectId(evento_id)})
    return serializar_evento(doc) if doc else None

def crear_evento(evento: EventoCreate):
    data = evento.model_dump()
    data["ubicacion"]["capacidad"] = int(data["ubicacion"]["capacidad"])
    for t in data["tickets_disponibles"]:
        t["stock_disponible"] = int(t["stock_disponible"])
    resultado = coleccion.insert_one(data)
    return obtener_evento(str(resultado.inserted_id))

def actualizar_evento(evento_id: str, evento: EventoUpdate):
    data = {k: v for k, v in evento.model_dump().items() if v is not None}
    if not data:
        return obtener_evento(evento_id)
    if "ubicacion" in data:
        data["ubicacion"]["capacidad"] = int(data["ubicacion"]["capacidad"])
    if "tickets_disponibles" in data:
        for t in data["tickets_disponibles"]:
            t["stock_disponible"] = int(t["stock_disponible"])
    coleccion.update_one({"_id": ObjectId(evento_id)}, {"$set": data})
    return obtener_evento(evento_id)

def eliminar_evento(evento_id: str) -> bool:
    res = coleccion.delete_one({"_id": ObjectId(evento_id)})
    return res.deleted_count > 0