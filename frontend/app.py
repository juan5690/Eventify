import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(page_title="Eventify Analytics", layout="wide")
st.title("🎟️ Eventify Global — Plataforma Analítica y Operativa")

# ----------------------------------------------------------
# 1. TARJETAS DE KPIs
# ----------------------------------------------------------
try:
    kpis = requests.get(f"{API_URL}/kpis", timeout=5).json()
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Volumen Total Recaudado", f"${kpis['volumen_total_recaudado']:,.0f} CLP")
    col2.metric("🧾 Ticket Promedio por Orden", f"${kpis['ticket_promedio']:,.0f} CLP", f"{kpis['total_ordenes']} órdenes")
    col3.metric("⭐ Satisfacción Promedio", f"{kpis['calificacion_promedio']} / 5.0", f"{kpis['total_resenas']} reseñas")
except Exception as e:
    st.error(f"No se pudo conectar con la API en {API_URL}. Error: {e}")
    st.stop()

st.divider()

tab_analitica, tab_crud = st.tabs(["📊 Consultas Analíticas", "⚙️ Administración de Eventos (CRUD)"])

# ----------------------------------------------------------
# 2. CONSULTAS ANALÍTICAS
# ----------------------------------------------------------
with tab_analitica:
    st.subheader("1. Distribución de Gasto Total por Ciudad")
    c1_data = requests.get(f"{API_URL}/consultas/gasto-ciudad").json()
    if c1_data:
        df_c1 = pd.DataFrame(c1_data)
        fig1 = px.bar(
            df_c1, x="ciudad", y="gasto_total_ciudad", text_auto=True,
            color="ciudad", title="Gasto Total Acumulado por Ciudad (CLP)",
            labels={"ciudad": "Ciudad", "gasto_total_ciudad": "Gasto Total ($ CLP)"}
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.divider()

    st.subheader("2. Reporte de Ventas y Rendimiento por Evento")
    c2_data = requests.get(f"{API_URL}/consultas/rendimiento-eventos").json()
    if c2_data:
        df_c2 = pd.DataFrame(c2_data)
        fig2 = px.bar(
            df_c2.head(15), x="titulo_evento", y="total_recaudado",
            color="etiqueta_rendimiento",
            hover_data=["ciudad", "porcentaje_ocupacion", "tickets_vendidos"],
            title="Top 15 Eventos por Recaudación y Clasificación de Rendimiento",
            labels={"titulo_evento": "Evento", "total_recaudado": "Recaudación ($ CLP)"}
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    st.subheader("3. Buscador Interactivo de Eventos Futuros Económicos")
    f_col1, f_col2 = st.columns(2)
    ciudad_sel = f_col1.selectbox("Selecciona Ciudad", ["Santiago", "Concepción", "Valparaíso", "Viña del Mar", "Temuco", "Antofagasta"])
    precio_sel = f_col2.slider("Precio Máximo del Ticket ($ CLP)", 5000, 100000, 30000, step=5000)

    c3_data = requests.get(
        f"{API_URL}/consultas/eventos-economicos",
        params={"ciudad": ciudad_sel, "precio_max": precio_sel}
    ).json()

    if c3_data:
        filas = []
        for ev in c3_data:
            for t in ev["tickets_economicos"]:
                filas.append({
                    "Evento": ev["titulo"],
                    "Categoría": ev["categoria"],
                    "Fecha": ev["fecha_evento"][:10],
                    "Dirección": ev["calle"],
                    "Tipo Ticket": t["tipo"],
                    "Precio ($)": t["precio"],
                    "Stock": t["stock_disponible"]
                })
        st.dataframe(pd.DataFrame(filas), use_container_width=True)
    else:
        st.info("No se encontraron eventos futuros bajo esos criterios.")

    st.divider()

    st.subheader("4. Análisis de Satisfacción por Evento")
    c4_data = requests.get(f"{API_URL}/consultas/satisfaccion").json()
    if c4_data:
        df_c4 = pd.DataFrame(c4_data)
        fig4 = px.scatter(
            df_c4, x="categoria", y="promedio_puntuacion",
            size="total_resenas", color="nivel_satisfaccion",
            hover_name="titulo_evento",
            title="Calificación Promedio por Categoría y Nivel de Satisfacción",
            labels={"categoria": "Categoría", "promedio_puntuacion": "Puntuación Promedio (1-5)"}
        )
        st.plotly_chart(fig4, use_container_width=True)

# ----------------------------------------------------------
# 3. GESTIÓN OPERATIVA (CRUD)
# ----------------------------------------------------------
with tab_crud:
    st.subheader("Gestión Operativa de Eventos")
    eventos = requests.get(f"{API_URL}/eventos/").json()
    df_ev = pd.DataFrame([
        {
            "ID": e["id"],
            "Título": e["titulo"],
            "Categoría": e["categoria"],
            "Fecha": e["fecha_evento"][:10],
            "Ciudad": e["ubicacion"]["ciudad"],
            "Capacidad": e["ubicacion"]["capacidad"]
        } for e in eventos
    ])
    st.dataframe(df_ev, use_container_width=True)

    col_crear, col_eliminar = st.columns(2)

    with col_crear:
        st.markdown("### ➕ Crear Nuevo Evento")
        with st.form("form_crear_evento"):
            titulo = st.text_input("Título del Evento")
            categoria = st.selectbox("Categoría", ["Concierto", "Festival", "Teatro", "Conferencia"])
            fecha = st.date_input("Fecha del Evento", datetime(2026, 12, 1))
            calle = st.text_input("Calle / Recinto")
            ciudad = st.text_input("Ciudad", "Santiago")
            capacidad = st.number_input("Capacidad", min_value=10, value=1000)
            precio_gen = st.number_input("Precio Ticket General", min_value=0, value=20000)
            stock_gen = st.number_input("Stock Ticket General", min_value=1, value=500)
            enviado = st.form_submit_button("Guardar Evento")

            if enviado and titulo and calle:
                payload = {
                    "titulo": titulo,
                    "categoria": categoria,
                    "fecha_evento": f"{fecha}T20:00:00Z",
                    "ubicacion": {
                        "calle": calle,
                        "ciudad": ciudad,
                        "coordenadas": [-70.65, -33.44],
                        "capacidad": int(capacidad)
                    },
                    "tickets_disponibles": [
                        {"tipo": "General", "precio": float(precio_gen), "stock_disponible": int(stock_gen)}
                    ]
                }
                res = requests.post(f"{API_URL}/eventos/", json=payload)
                if res.status_code == 201:
                    st.success("Evento creado exitosamente.")
                    st.rerun()
                else:
                    st.error(f"Error al crear: {res.text}")

    with col_eliminar:
        st.markdown("### 🗑️ Eliminar Evento")
        with st.form("form_eliminar_evento"):
            id_borrar = st.selectbox("Selecciona ID del Evento a eliminar", df_ev["ID"].tolist() if not df_ev.empty else [])
            confirmar = st.form_submit_button("Eliminar Evento")
            if confirmar and id_borrar:
                res = requests.delete(f"{API_URL}/eventos/{id_borrar}")
                if res.status_code == 200:
                    st.success("Evento eliminado correctamente.")
                    st.rerun()
                else:
                    st.error(f"Error al eliminar: {res.text}")