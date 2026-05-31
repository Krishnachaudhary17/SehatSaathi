import asyncio
from sqlalchemy import text
from database import engine

async def check():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT id, name, email FROM users WHERE role='doctor' LIMIT 5"))
        print("=== Doctor Users ===")
        for row in r:
            print(row)

        r2 = await conn.execute(text("SELECT id, name, user_id, specialty FROM doctors WHERE user_id IS NOT NULL LIMIT 5"))
        print("=== Doctors with user_id linked ===")
        for row in r2:
            print(row)

        r3 = await conn.execute(text("SELECT id, doctor_id, doctor_name, user_id, status FROM appointments LIMIT 5"))
        print("=== Appointments ===")
        for row in r3:
            print(row)

asyncio.run(check())
