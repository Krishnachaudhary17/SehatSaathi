"""
models.py — SQLAlchemy ORM models (maps to PostgreSQL tables)
"""

import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, Date, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base


# ─────────────────────────────────────────────
#  USERS
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(5), default="en")
    role: Mapped[str] = mapped_column(String(20), default="patient")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship: one user → many records
    records: Mapped[list["Record"]] = relationship("Record", back_populates="user")


# ─────────────────────────────────────────────
#  MEDICAL RECORDS
# ─────────────────────────────────────────────
class Record(Base):
    __tablename__ = "records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255))
    date: Mapped[datetime] = mapped_column(Date, nullable=True)
    type: Mapped[str] = mapped_column(String(50))       # Prescription / Lab Report / etc.
    doctor: Mapped[str] = mapped_column(String(150), default="Self Uploaded")
    status: Mapped[str] = mapped_column(String(50), default="Saved")
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="records")


# ─────────────────────────────────────────────
#  DOCTORS
# ─────────────────────────────────────────────
class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Links to a registered user account (nullable for seeded/legacy doctors)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    name: Mapped[str] = mapped_column(String(150))
    specialty: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(255), default="India")
    lat: Mapped[float] = mapped_column(Float, nullable=True)
    lng: Mapped[float] = mapped_column(Float, nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    available: Mapped[bool] = mapped_column(Boolean, default=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    experience_years: Mapped[int] = mapped_column(default=0)
    fee: Mapped[int] = mapped_column(default=500)            # consultation fee in INR
    bio: Mapped[str] = mapped_column(Text, nullable=True)


# ─────────────────────────────────────────────
#  APPOINTMENTS
# ─────────────────────────────────────────────
class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    doctor_name: Mapped[str] = mapped_column(String(150))
    specialty: Mapped[str] = mapped_column(String(100))
    hospital: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    fee: Mapped[int] = mapped_column(default=0)
    appt_date: Mapped[datetime] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    doctor: Mapped["User"] = relationship("User", foreign_keys=[doctor_id])


# ─────────────────────────────────────────────
#  MESSAGES (Doctor ↔ Patient Chat)
# ─────────────────────────────────────────────
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="CASCADE")
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    sender_name: Mapped[str] = mapped_column(String(100))
    sender_role: Mapped[str] = mapped_column(String(20))   # "patient" or "doctor"
    content: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
#  MEDICINES
# ─────────────────────────────────────────────
class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    brand_names: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(100), index=True)
    medicine_type: Mapped[str] = mapped_column(String(50))
    active_ingredients: Mapped[str] = mapped_column(Text)
    uses: Mapped[str] = mapped_column(Text)
    side_effects: Mapped[str] = mapped_column(Text)
    dosage: Mapped[str] = mapped_column(Text)
    precautions: Mapped[str] = mapped_column(Text, nullable=True)
    contraindications: Mapped[str] = mapped_column(Text, nullable=True)
    is_otc: Mapped[bool] = mapped_column(Boolean, default=True)
    emoji: Mapped[str] = mapped_column(String(10), default="💊")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
