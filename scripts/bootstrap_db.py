"""
SecureDocAI — Database Bootstrap Script
===========================================
Creates the database tables and inserts default users.
Run this script manually when initializing a fresh environment.
"""

import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import SessionLocal, init_db
from app.models.user import User
from app.core.security import hash_password

def bootstrap() -> None:
    # 1. Initialize Tables
    print("Initializing Database Tables...")
    init_db()

    # 2. Insert Default Users
    db = SessionLocal()
    try:
        # Check if users already exist
        if db.query(User).first():
            print("Users already exist in the database. Skipping creation.")
            return

        print("Creating default 'admin' and 'operator' users...")
        users = [
            User(
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin",
                is_active=True,
            ),
            User(
                username="operator",
                hashed_password=hash_password("operator123"),
                role="operator",
                is_active=True,
            )
        ]
        db.add_all(users)
        db.commit()
        print("Successfully created default users.")
    except Exception as e:
        db.rollback()
        print(f"Failed to bootstrap users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    bootstrap()
