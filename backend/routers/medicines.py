"""
routers/medicines.py — Public medicine reference API (no auth required)
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import Optional

from database import get_db
from models import Medicine
from schemas import MedicineOut

router = APIRouter(prefix="/api/medicines", tags=["Medicines"])


@router.get("", response_model=list[MedicineOut])
async def list_medicines(
    search: Optional[str] = Query(None, description="Search by name, brand, or use"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Medicine)

    if search:
        term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(Medicine.name).like(term),
                func.lower(Medicine.brand_names).like(term),
                func.lower(Medicine.uses).like(term),
                func.lower(Medicine.category).like(term),
                func.lower(Medicine.active_ingredients).like(term),
            )
        )

    if category and category != "All":
        query = query.where(Medicine.category == category)

    query = query.order_by(Medicine.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/categories", response_model=list[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Medicine.category).distinct().order_by(Medicine.category)
    )
    return [row[0] for row in result.all()]


@router.get("/{medicine_id}", response_model=MedicineOut)
async def get_medicine(medicine_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Medicine).where(Medicine.id == medicine_id))
    med = result.scalar_one_or_none()
    if not med:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Medicine not found.")
    return med
