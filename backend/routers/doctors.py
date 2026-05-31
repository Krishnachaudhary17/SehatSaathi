"""
routers/doctors.py — Doctor search, listing, and profile management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional

from database import get_db
from models import Doctor, Appointment
from schemas import DoctorOut, DoctorUpdate
from auth import get_current_user

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


@router.patch("/me", response_model=DoctorOut)
async def update_my_profile(
    body: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not a doctor")
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(doctor, field, value)

    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.get("/conversations")
async def get_my_conversations(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Returns all unique patient appointments for the doctor's chat page."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Not a doctor")

    from models import User
    from sqlalchemy import text

    doc_res = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor_profile = doc_res.scalar_one_or_none()

    conditions = [Appointment.doctor_id == current_user.id]
    if doctor_profile:
        name_part = doctor_profile.name.replace("Dr. ", "").strip()
        conditions.append(Appointment.doctor_name.ilike(f"%{name_part}%"))

    result = await db.execute(
        select(Appointment)
        .where(or_(*conditions))
        .order_by(Appointment.created_at.desc())
    )

    seen = set()
    appts = []
    for a in result.scalars().all():
        if a.id not in seen:
            seen.add(a.id)
            appts.append(a)

    # Fetch patient names
    from models import User as UserModel
    patient_ids = list({a.user_id for a in appts if a.user_id})
    patient_map = {}
    if patient_ids:
        users_res = await db.execute(select(UserModel).where(UserModel.id.in_(patient_ids)))
        for u in users_res.scalars().all():
            patient_map[u.id] = {"name": u.name, "email": u.email}

    return [
        {
            "appt_id": str(a.id),
            "patient_name": patient_map.get(a.user_id, {}).get("name", "Unknown Patient"),
            "patient_email": patient_map.get(a.user_id, {}).get("email", ""),
            "appt_date": str(a.appt_date),
            "specialty": a.specialty,
            "status": a.status,
            "reason": a.reason or "",
        }
        for a in appts
    ]


@router.get("", response_model=list[DoctorOut])
async def get_doctors(
    specialty: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Doctor).order_by(Doctor.rating.desc())

    if specialty and specialty.lower() != "all":
        query = query.where(Doctor.specialty.ilike(f"%{specialty}%"))

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
