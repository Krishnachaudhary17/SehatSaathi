"""
Fix existing appointments: link doctor_id by matching doctor_name to registered doctor users.
Run once: python fix_appointments.py
"""
import asyncio
from sqlalchemy import text
from database import engine

async def fix():
    async with engine.begin() as conn:
        # Get all doctor users and their doctor profiles
        result = await conn.execute(text("""
            SELECT u.id as user_id, d.name as doctor_name
            FROM users u
            JOIN doctors d ON d.user_id = u.id
            WHERE u.role = 'doctor'
        """))
        doctors = result.fetchall()
        print(f"Found {len(doctors)} registered doctors with profiles")
        
        fixed = 0
        for doctor in doctors:
            user_id = doctor[0]
            doc_name = doctor[1]  # e.g. "Dr. Chaudhary"
            # Strip "Dr. " prefix for fuzzy matching
            name_part = doc_name.replace("Dr. ", "").strip()
            
            # Update appointments where doctor_name matches but doctor_id is NULL
            update_result = await conn.execute(text("""
                UPDATE appointments
                SET doctor_id = :user_id
                WHERE doctor_id IS NULL
                AND (
                    doctor_name ILIKE :full_name
                    OR doctor_name ILIKE :name_part
                )
            """), {"user_id": user_id, "full_name": f"%{doc_name}%", "name_part": f"%{name_part}%"})
            
            n = update_result.rowcount
            if n > 0:
                print(f"  Linked {n} appointments to {doc_name} (user_id={user_id})")
                fixed += n
        
        print(f"\nTotal appointments fixed: {fixed}")
        
        # Show current state
        r = await conn.execute(text("""
            SELECT doctor_name, doctor_id, status FROM appointments ORDER BY created_at DESC LIMIT 10
        """))
        print("\n=== Current Appointments ===")
        for row in r:
            print(f"  {row[0]} | doctor_id={row[1]} | {row[2]}")

asyncio.run(fix())
