"""
routers/appointments.py — Appointments CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from typing import Any

from database import get_db
from models import Appointment, Doctor, User
from schemas import AppointmentCreate, AppointmentOut
from auth import get_current_user

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Auto-resolve doctor_id: try to find a registered doctor matching the name
    resolved_doctor_id = body.doctor_id
    matched_doctor = None

    if resolved_doctor_id is None:
        name_part = body.doctor_name.replace("Dr. ", "").strip()
        res = await db.execute(
            select(Doctor).where(
                Doctor.user_id.is_not(None),
                or_(
                    Doctor.name.ilike(f"%{body.doctor_name}%"),
                    Doctor.name.ilike(f"%{name_part}%")
                )
            )
        )
        matched_doctor = res.scalar_one_or_none()
        if matched_doctor:
            resolved_doctor_id = matched_doctor.user_id
    else:
        # Fetch by doctor_id to check availability
        res = await db.execute(
            select(Doctor).where(Doctor.user_id == resolved_doctor_id)
        )
        matched_doctor = res.scalar_one_or_none()

    # If we found the doctor in the DB, check availability
    if matched_doctor is not None and not matched_doctor.available:
        raise HTTPException(
            status_code=409,
            detail=f"{body.doctor_name} is currently unavailable. Please choose another doctor."
        )

    # Also look up by name even without user_id link (seeded doctors)
    if matched_doctor is None:
        name_part = body.doctor_name.replace("Dr. ", "").strip()
        res = await db.execute(
            select(Doctor).where(
                or_(
                    Doctor.name.ilike(f"%{body.doctor_name}%"),
                    Doctor.name.ilike(f"%{name_part}%")
                )
            )
        )
        matched_doctor = res.scalar_one_or_none()
        if matched_doctor is not None and not matched_doctor.available:
            raise HTTPException(
                status_code=409,
                detail=f"{body.doctor_name} is currently unavailable. Please choose another doctor."
            )

    appt = Appointment(
        user_id=current_user.id,
        doctor_id=resolved_doctor_id,
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

    # Get doctor's profile name
    doc_res = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor_profile = doc_res.scalar_one_or_none()

    # Match by doctor_id OR by name
    conditions = [Appointment.doctor_id == current_user.id]
    if doctor_profile:
        name_part = doctor_profile.name.replace("Dr. ", "").strip()
        conditions.append(Appointment.doctor_name.ilike(f"%{name_part}%"))

    result = await db.execute(
        select(Appointment)
        .where(or_(*conditions))
        .order_by(Appointment.appt_date.asc())
    )

    # Deduplicate + enrich with patient names
    seen = set()
    appts = []
    for a in result.scalars().all():
        if a.id in seen:
            continue
        seen.add(a.id)
        appts.append(a)

    # Fetch patient names in one query
    patient_ids = list({a.user_id for a in appts if a.user_id})
    patient_map = {}
    if patient_ids:
        users_res = await db.execute(select(User).where(User.id.in_(patient_ids)))
        for u in users_res.scalars().all():
            patient_map[u.id] = u.name

    # Build enriched response
    output = []
    for a in appts:
        item = AppointmentOut.model_validate(a)
        item.patient_name = patient_map.get(a.user_id, "Unknown Patient")
        output.append(item)

    return output


@router.patch("/{appt_id}/status", response_model=AppointmentOut)
async def update_appointment_status(
    appt_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Doctor can mark appointments as Completed or Cancelled."""
    result = await db.execute(select(Appointment).where(Appointment.id == appt_id))
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if current_user.role == "doctor":
        doc_res = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
        doc = doc_res.scalar_one_or_none()
        is_their_appt = (
            appt.doctor_id == current_user.id or
            (doc and appt.doctor_name and doc.name.lower() in appt.doctor_name.lower())
        )
        if not is_their_appt:
            raise HTTPException(status_code=403, detail="Not your appointment.")
    elif appt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    new_status = body.get("status", "Cancelled")
    if new_status not in ("Confirmed", "Cancelled", "Completed"):
        raise HTTPException(status_code=400, detail="Invalid status.")
    appt.status = new_status
    await db.commit()
    await db.refresh(appt)
    return appt


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
