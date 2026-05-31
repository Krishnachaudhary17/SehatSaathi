"""
main.py — FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base
from routers import auth, records, chat, doctors, appointments, medicines, rehab, messages

app = FastAPI(title="Sehat Saathi")

# Serve uploaded files
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth.router)
app.include_router(records.router)
app.include_router(chat.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(medicines.router)
app.include_router(rehab.router)
app.include_router(messages.router)


@app.on_event("startup")
async def startup_event():
    # In a real app, use Alembic for migrations.
    # For quick prototyping, we'll auto-create tables if they don't exist.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Mount the frontend directory to serve HTML/CSS/JS
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
