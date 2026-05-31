import asyncio
from database import engine
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE messages ADD COLUMN message_type VARCHAR(20) DEFAULT 'text'"))
            print("OK: Added message_type column to messages")
        except Exception as e:
            print("Skipped (may already exist):", e)

asyncio.run(migrate())
