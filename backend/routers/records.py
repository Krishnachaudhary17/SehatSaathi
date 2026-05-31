"""
routers/records.py — CRUD for medical records
"""

import os
import uuid
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import Record, User
from schemas import RecordOut
from auth import get_current_user

router = APIRouter(prefix="/api/records", tags=["Records"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Icon map (mirrors the frontend logic)
ICON_MAP = {
    "Prescription": "💊",
    "Lab Report": "🧪",
    "Discharge Report": "🏥",
    "Imaging": "🩻",
    "Report": "📄",
}


@router.get("", response_model=list[RecordOut])
async def get_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Record)
        .where(Record.user_id == current_user.id)
        .order_by(Record.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=RecordOut, status_code=201)
async def upload_record(
    name: str = Form(...),
    type: str = Form(...),
    doctor: str = Form("Self Uploaded"),
    record_date: str = Form(None),
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Save file if provided
    file_path = None
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        full_path = os.path.join(UPLOAD_DIR, filename)
        with open(full_path, "wb") as f:
            content = await file.read()
            f.write(content)
        file_path = f"uploads/{filename}"

    # Parse date
    parsed_date = None
    if record_date:
        try:
            parsed_date = date.fromisoformat(record_date)
        except ValueError:
            pass

    record = Record(
        user_id=current_user.id,
        name=name,
        date=parsed_date,
        type=type,
        doctor=doctor,
        status="Saved",
        file_path=file_path,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
async def delete_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Record).where(Record.id == record_id, Record.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")

    # Remove file from disk if it exists
    if record.file_path:
        full_path = os.path.join(os.path.dirname(__file__), "..", record.file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    await db.delete(record)
    await db.commit()
