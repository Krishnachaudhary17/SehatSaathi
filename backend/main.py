"""
main.py — FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from database import engine, Base, AsyncSessionLocal
from routers import auth, records, chat, doctors, appointments, medicines, rehab, messages
from models import Medicine, Doctor
from sqlalchemy import select, func

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
    # Auto-create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-seed medicines if table is empty
    async with AsyncSessionLocal() as session:
        med_count = await session.scalar(select(func.count()).select_from(Medicine))
        if med_count == 0:
            print("🌱 Seeding medicines table...")
            from seed_medicines import MEDICINES
            for m in MEDICINES:
                session.add(Medicine(**m))
            await session.commit()
            print(f"✅ Seeded {len(MEDICINES)} medicines.")

        # Auto-seed doctors (static/demo doctors only) if table is empty
        doc_count = await session.scalar(select(func.count()).select_from(Doctor))
        if doc_count == 0:
            print("🌱 Seeding doctors table...")
            from seed_doctors import DOCTORS
            for d in DOCTORS:
                session.add(Doctor(**d))
            await session.commit()
            print(f"✅ Seeded {len(DOCTORS)} doctors.")


# Mount the frontend directory to serve HTML/CSS/JS
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

