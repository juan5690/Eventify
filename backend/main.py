from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.controllers import eventos_controller, analytics_controller

app = FastAPI(
    title="Eventify Global API",
    description="API REST para gestión operativa y analítica de Eventify (MongoDB + FastAPI)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(eventos_controller.router)
app.include_router(analytics_controller.router)

@app.get("/")
def root():
    return {"estado": "API Eventify operativa", "docs": "/docs"}