
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import init_db


async def main():
    print("Creating database tables...")
    await init_db()
    print("Database tables created successfully!")
    print("- users")
    print("- conversations")
    print("- messages")


if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("\nDatabase initialization complete!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

