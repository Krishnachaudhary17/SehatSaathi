"""
routers/appointments.py — Appointments CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from database import get_db
from models import Appointment
from schemas import AppointmentCreate, AppointmentOut
from auth import get_current_user

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    appt = Appointment(
        user_id=current_user.id,
        doctor_id=body.doctor_id,
        doctor_name=body.doctor_name,
        specialty=body.specialty,
        hospital=body.hospital,
        phone=body.phone,
        fee=body.fee or 0,
        appt_date=body.appt_date,
        reason=body.reason,
        status="Confirmed",
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    return appt


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment)
        .where(Appointment.user_id == current_user.id)
        .order_by(Appointment.appt_date.desc())
    )
    return result.scalars().all()


@router.get("/schedule", response_model=list[AppointmentOut])
async def doctor_schedule(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view their schedule.")
        
    result = await db.execute(
        select(Appointment)
        .where(Appointment.doctor_id == current_user.id)
        .order_by(Appointment.appt_date.asc())
    )
    return result.scalars().all()


@router.patch("/{appt_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appt_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appt_id,
            Appointment.user_id == current_user.id,
        )
    )
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    appt.status = "Cancelled"
    await db.commit()
    await db.refresh(appt)
    return appt
