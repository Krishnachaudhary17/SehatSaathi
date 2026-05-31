"""
schemas.py — Pydantic models for request validation and response serialization
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from uuid import UUID


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    language: Optional[str] = "en"
    role: Optional[str] = "patient"
    specialty: Optional[str] = "General"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: UUID
    name: str
    email: str
    language: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  RECORDS
# ─────────────────────────────────────────────
class RecordOut(BaseModel):
    id: UUID
    name: str
    date: Optional[date]
    type: str
    doctor: str
    status: str
    file_path: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  AI CHAT
# ─────────────────────────────────────────────
class ChatResponse(BaseModel):
    reply: str


# ─────────────────────────────────────────────
#  MESSAGES (Doctor-Patient Chat)
# ─────────────────────────────────────────────
class MessageCreate(BaseModel):
    content: str
    message_type: Optional[str] = "text"  # text / prescription

class MessageOut(BaseModel):
    id: int
    appointment_id: UUID
    sender_id: UUID
    sender_name: str
    sender_role: str
    message_type: str
    content: str
    sent_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  DOCTORS
# ─────────────────────────────────────────────
class DoctorOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    name: str
    specialty: str
    location: str
    lat: Optional[float]
    lng: Optional[float]
    rating: float
    available: bool
    phone: Optional[str]
    experience_years: int
    fee: int
    bio: Optional[str]

    model_config = {"from_attributes": True}


class DoctorUpdate(BaseModel):
    specialty: Optional[str] = None
    fee: Optional[int] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    experience_years: Optional[int] = None
    available: Optional[bool] = None


# ─────────────────────────────────────────────
#  APPOINTMENTS
# ─────────────────────────────────────────────
class AppointmentCreate(BaseModel):
    doctor_id: Optional[UUID] = None
    doctor_name: str
    specialty: str
    hospital: str
    phone: Optional[str] = None
    fee: Optional[int] = 0
    appt_date: date
    reason: Optional[str] = None


class AppointmentOut(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    doctor_id: Optional[UUID] = None
    patient_name: Optional[str] = None   # populated by doctor schedule endpoint
    doctor_name: str
    specialty: str
    hospital: str
    phone: Optional[str]
    fee: int
    appt_date: date
    reason: Optional[str]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  MEDICINES
# ─────────────────────────────────────────────
class MedicineOut(BaseModel):
    id: int
    name: str
    brand_names: Optional[str]
    category: str
    medicine_type: str
    active_ingredients: str
    uses: str
    side_effects: str
    dosage: str
    precautions: Optional[str]
    contraindications: Optional[str]
    is_otc: bool
    emoji: str

    model_config = {"from_attributes": True}
