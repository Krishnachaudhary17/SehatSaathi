import asyncio
from sqlalchemy import text
from database import engine

async def alter_db():
    async with engine.begin() as conn:
        print("Adding user_id to doctors table...")
        try:
            await conn.execute(text("ALTER TABLE doctors ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE SET NULL UNIQUE;"))
            print("Successfully added user_id.")
        except Exception as e:
            print("Error or already exists:", e)
        
        print("Creating messages table...")
        try:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
                sender_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                sender_name VARCHAR(100) NOT NULL,
                sender_role VARCHAR(20) NOT NULL,
                content TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))
            print("Successfully created messages table.")
        except Exception as e:
            print("Error creating messages table:", e)

if __name__ == "__main__":
    asyncio.run(alter_db())
