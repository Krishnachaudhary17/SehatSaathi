"""
routers/doctors.py — Doctor search and listing
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from database import get_db
from models import Doctor
from schemas import DoctorOut
from auth import get_current_user
from fastapi import HTTPException

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

@router.get("/me", response_model=DoctorOut)
async def get_my_doctor_profile(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not a doctor")
        
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
        
    return doctor


@router.get("", response_model=list[DoctorOut])
async def get_doctors(
    specialty: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Doctor).order_by(Doctor.rating.desc())

    # Filter by specialty tab
    if specialty and specialty.lower() != "all":
        query = query.where(Doctor.specialty.ilike(f"%{specialty}%"))

    # Free-text search across name, specialty, location
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Doctor.name.ilike(term),
                Doctor.specialty.ilike(term),
                Doctor.location.ilike(term),
            )
        )

    result = await db.execute(query)
    return result.scalars().all()
