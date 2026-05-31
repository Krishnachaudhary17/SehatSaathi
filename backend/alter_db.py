import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)

async def alter_tables():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'patient';"))
            print("Added role to users")
        except Exception as e:
            print("users alter error:", e)
            
        try:
            await conn.execute(text("ALTER TABLE appointments ADD COLUMN doctor_id UUID REFERENCES users(id) ON DELETE SET NULL;"))
            print("Added doctor_id to appointments")
        except Exception as e:
            print("appointments alter error:", e)

if __name__ == "__main__":
    asyncio.run(alter_tables())
