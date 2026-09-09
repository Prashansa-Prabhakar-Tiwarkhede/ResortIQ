import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.services.realtime import manager
from app.api import (
    auth_router, dashboard_router, maintenance_router, recommendations_router,
    tasks_router, alerts_router, guest_router, inventory_router, staffing_router, revenue_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ResortIQ API", version="0.1.0",
              description="AI-Powered Resort Operations, Guest Experience & Revenue Intelligence")

ALLOWED_ORIGINS = [
    "https://resort-iq-d2q1.vercel.app",
    "https://resort-iq-eta.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]

env_origins = os.getenv("ALLOWED_ORIGINS")
if env_origins:
    ALLOWED_ORIGINS.extend([origin.strip() for origin in env_origins.split(",") if origin.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https:\/\/resort-iq-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(dashboard_router.router)
app.include_router(maintenance_router.router)
app.include_router(recommendations_router.router)
app.include_router(tasks_router.router)
app.include_router(alerts_router.router)
app.include_router(guest_router.router)
app.include_router(inventory_router.router)
app.include_router(staffing_router.router)
app.include_router(revenue_router.router)


@app.on_event("startup")
async def on_startup():
    try:
        manager.set_loop(asyncio.get_running_loop())
    except Exception:
        pass
    try:
        from seed import ensure_seeded
        ensure_seeded()
    except Exception as e:
        print(f"Startup seed notice: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive; content ignored
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
def root():
    return {"status": "ok", "service": "ResortIQ API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
