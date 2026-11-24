from datetime import datetime
from typing import Optional
from backend.database import get_db

db = get_db()

# ---------------------------------------------------------
# KPIs DE NEGOCIO (/api/v1/kpis)
# ---------------------------------------------------------
def obtener_kpis():
    ordenes_agg = list(db["ordenes_compra"].aggregate([
        {
            "$group": {
                "_id": None,
                "volumen_total_recaudado": {"$sum": "$monto_total"},
                "ticket_promedio": {"$avg": "$monto_total"},
                "total_ordenes": {"$sum": 1}
            }
        }
    ]))

    resenas_agg = list(db["resenas_evaluaciones"].aggregate([
        {
            "$group": {
                "_id": None,
                "calificacion_promedio": {"$avg": "$puntuacion"},
                "total_resenas": {"$sum": 1}
            }
        }
    ]))

    ordenes_data = ordenes_agg[0] if ordenes_agg else {}
    resenas_data = resenas_agg[0] if resenas_agg else {}

    return {
        "volumen_total_recaudado": round(ordenes_data.get("volumen_total_recaudado", 0), 2),
        "ticket_promedio": round(ordenes_data.get("ticket_promedio", 0), 2),
        "total_ordenes": ordenes_data.get("total_ordenes", 0),
        "calificacion_promedio": round(resenas_data.get("calificacion_promedio", 0), 2),
        "total_resenas": resenas_data.get("total_resenas", 0)
    }

# ---------------------------------------------------------
# CONSULTA 1: Gasto por usuario y ciudad ($lookup + $unwind)
# ---------------------------------------------------------
def consulta_1_gasto_ciudad(correo: Optional[str] = None, ciudad: Optional[str] = None):
    pipeline = [
        {
            "$lookup": {
                "from": "usuarios",
                "localField": "usuario_id",
                "foreignField": "_id",
                "as": "detalles_usuario"
            }
        },
        {"$unwind": "$detalles_usuario"},
    ]

    if correo:
        pipeline.append({"$match": {"detalles_usuario.correo": correo}})

    pipeline.extend([
        {
            "$lookup": {
                "from": "eventos",
                "localField": "evento_id",
                "foreignField": "_id",
                "as": "detalles_evento"
            }
        },
        {"$unwind": "$detalles_evento"},
    ])

    if ciudad:
        pipeline.append({"$match": {"detalles_evento.ubicacion.ciudad": ciudad}})

    pipeline.extend([
        {"$unwind": "$items_comprados"},
        {
            "$project": {
                "_id": 0,
                "orden_id": {"$toString": "$_id"},
                "fecha_transaccion": 1,
                "usuario": "$detalles_usuario.nombre",
                "correo": "$detalles_usuario.correo",
                "titulo_evento": "$detalles_evento.titulo",
                "categoria_evento": "$detalles_evento.categoria",
                "ciudad_evento": "$detalles_evento.ubicacion.ciudad",
                "tipo_ticket": "$items_comprados.tipo_ticket",
                "cantidad": "$items_comprados.cantidad",
                "subtotal": "$items_comprados.subtotal",
                "monto_total_orden": "$monto_total"
            }
        },
        {
            "$group": {
                "_id": "$ciudad_evento",
                "gasto_total_ciudad": {"$sum": "$monto_total_orden"},
                "cantidad_compras": {"$sum": 1},
                "compras_realizadas": {"$push": "$$ROOT"}
            }
        },
        {"$sort": {"gasto_total_ciudad": -1}}
    ])

    resultados = list(db["ordenes_compra"].aggregate(pipeline))
    for r in resultados:
        r["ciudad"] = r.pop("_id")
        for c in r["compras_realizadas"]:
            if hasattr(c.get("fecha_transaccion"), "isoformat"):
                c["fecha_transaccion"] = c["fecha_transaccion"].isoformat()
    return resultados

# ---------------------------------------------------------
# CONSULTA 2: Reporte de ventas y rendimiento por evento
# ---------------------------------------------------------
def consulta_2_rendimiento_eventos():
    pipeline = [
        {
            "$group": {
                "_id": "$evento_id",
                "total_recaudado": {"$sum": "$monto_total"},
                "tickets_vendidos": {
                    "$sum": {
                        "$reduce": {
                            "input": "$items_comprados",
                            "initialValue": 0,
                            "in": {"$add": ["$$value", "$$this.cantidad"]}
                        }
                    }
                }
            }
        },
        {
            "$lookup": {
                "from": "eventos",
                "localField": "_id",
                "foreignField": "_id",
                "as": "info_evento"
            }
        },
        {"$unwind": "$info_evento"},
        {
            "$addFields": {
                "titulo_evento": "$info_evento.titulo",
                "ciudad": "$info_evento.ubicacion.ciudad",
                "stock_restante_total": {"$sum": "$info_evento.tickets_disponibles.stock_disponible"}
            }
        },
        {
            "$addFields": {
                "stock_inicial_total": {"$add": ["$tickets_vendidos", "$stock_restante_total"]}
            }
        },
        {
            "$addFields": {
                "porcentaje_ocupacion": {
                    "$cond": {
                        "if": {"$gt": ["$stock_inicial_total", 0]},
                        "then": {"$multiply": [{"$divide": ["$tickets_vendidos", "$stock_inicial_total"]}, 100]},
                        "else": 0
                    }
                }
            }
        },
        {
            "$addFields": {
                "etiqueta_rendimiento": {
                    "$cond": {
                        "if": {"$gte": ["$porcentaje_ocupacion", 20]},
                        "then": "Exitoso",
                        "else": "Por Mejorar"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "evento_id": {"$toString": "$_id"},
                "titulo_evento": 1,
                "ciudad": 1,
                "total_recaudado": 1,
                "tickets_vendidos": 1,
                "stock_restante_total": 1,
                "stock_inicial_total": 1,
                "porcentaje_ocupacion": {"$round": ["$porcentaje_ocupacion", 2]},
                "etiqueta_rendimiento": 1
            }
        },
        {"$sort": {"total_recaudado": -1}}
    ]
    return list(db["ordenes_compra"].aggregate(pipeline))

# ---------------------------------------------------------
# CONSULTA 3: Eventos futuros por ciudad y precio máximo
# ---------------------------------------------------------
def consulta_3_eventos_economicos(ciudad: str = "Santiago", precio_max: float = 30000, fecha_desde: str = "2026-06-01"):
    fecha_dt = datetime.fromisoformat(fecha_desde)
    pipeline = [
        {
            "$match": {
                "fecha_evento": {"$gte": fecha_dt},
                "ubicacion.ciudad": ciudad,
                "tickets_disponibles.precio": {"$lt": precio_max}
            }
        },
        {
            "$project": {
                "_id": 0,
                "evento_id": {"$toString": "$_id"},
                "titulo": 1,
                "categoria": 1,
                "fecha_evento": 1,
                "ciudad": "$ubicacion.ciudad",
                "calle": "$ubicacion.calle",
                "tickets_economicos": {
                    "$filter": {
                        "input": "$tickets_disponibles",
                        "as": "ticket",
                        "cond": {"$lt": ["$$ticket.precio", precio_max]}
                    }
                }
            }
        }
    ]
    resultados = list(db["eventos"].aggregate(pipeline))
    for r in resultados:
        if hasattr(r.get("fecha_evento"), "isoformat"):
            r["fecha_evento"] = r["fecha_evento"].isoformat()
    return resultados

# ---------------------------------------------------------
# CONSULTA 4: Análisis de satisfacción por evento
# ---------------------------------------------------------
def consulta_4_satisfaccion():
    pipeline = [
        {
            "$group": {
                "_id": "$evento_id",
                "promedio_puntuacion": {"$avg": "$puntuacion"},
                "total_resenas": {"$sum": 1}
            }
        },
        {"$match": {"total_resenas": {"$gte": 1}}},
        {
            "$lookup": {
                "from": "eventos",
                "localField": "_id",
                "foreignField": "_id",
                "as": "detalles_evento"
            }
        },
        {"$unwind": "$detalles_evento"},
        {
            "$addFields": {
                "nivel_satisfaccion": {
                    "$cond": {
                        "if": {"$gte": ["$promedio_puntuacion", 4.0]},
                        "then": "Altamente Recomendado",
                        "else": "Requiere Mejora"
                    }
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "evento_id": {"$toString": "$_id"},
                "titulo_evento": "$detalles_evento.titulo",
                "categoria": "$detalles_evento.categoria",
                "ciudad": "$detalles_evento.ubicacion.ciudad",
                "promedio_puntuacion": {"$round": ["$promedio_puntuacion", 2]},
                "total_resenas": 1,
                "nivel_satisfaccion": 1
            }
        },
        {"$sort": {"promedio_puntuacion": -1}}
    ]
    return list(db["resenas_evaluaciones"].aggregate(pipeline))