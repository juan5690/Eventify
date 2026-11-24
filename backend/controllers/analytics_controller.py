from fastapi import APIRouter, Query
from typing import Optional
from backend.services import analytics_service

router = APIRouter(prefix="/api/v1", tags=["Analítica y KPIs"])

@router.get("/kpis")
def get_kpis():
    return analytics_service.obtener_kpis()

@router.get("/consultas/gasto-ciudad")
def get_consulta_1(
    correo: Optional[str] = Query(None, description="Filtrar por correo de usuario"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad")
):
    return analytics_service.consulta_1_gasto_ciudad(correo=correo, ciudad=ciudad)

@router.get("/consultas/rendimiento-eventos")
def get_consulta_2():
    return analytics_service.consulta_2_rendimiento_eventos()

@router.get("/consultas/eventos-economicos")
def get_consulta_3(
    ciudad: str = Query("Santiago", description="Ciudad del evento"),
    precio_max: float = Query(30000, description="Precio máximo del ticket"),
    fecha_desde: str = Query("2026-06-01", description="Fecha mínima (YYYY-MM-DD)")
):
    return analytics_service.consulta_3_eventos_economicos(ciudad, precio_max, fecha_desde)

@router.get("/consultas/satisfaccion")
def get_consulta_4():
    return analytics_service.consulta_4_satisfaccion()