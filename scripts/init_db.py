
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models import user, conversation, message


def init_database():
    print("Creating database tables...")
    
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    print("- users")
    print("- conversations")
    print("- messages")


if __name__ == "__main__":
    try:
        init_database()
        print("\nDatabase initialization complete!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

