"""
routers/messages.py — Chat messages between patient and doctor
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from database import get_db
from models import Message, Appointment
from schemas import MessageCreate, MessageOut
from auth import get_current_user

router = APIRouter(prefix="/api/messages", tags=["Messages"])

@router.get("/{appointment_id}", response_model=list[MessageOut])
async def get_messages(
    appointment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Verify access to this appointment
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.id not in [appt.user_id, appt.doctor_id]:
        raise HTTPException(status_code=403, detail="Not authorized to view these messages")
        
    # Fetch messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.appointment_id == appointment_id)
        .order_by(Message.sent_at.asc())
    )
    return msg_result.scalars().all()


@router.post("/{appointment_id}", response_model=MessageOut)
async def send_message(
    appointment_id: UUID,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Verify access
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appt = result.scalar_one_or_none()
    
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
        
    if current_user.id not in [appt.user_id, appt.doctor_id]:
        raise HTTPException(status_code=403, detail="Not authorized to send messages here")
        
    new_msg = Message(
        appointment_id=appointment_id,
        sender_id=current_user.id,
        sender_name=current_user.name,
        sender_role=current_user.role,
        message_type=body.message_type or "text",
        content=body.content
    )
    
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    
    return new_msg
