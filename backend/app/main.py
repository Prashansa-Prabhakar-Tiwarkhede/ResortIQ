import asyncio
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    manager.set_loop(asyncio.get_running_loop())


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
