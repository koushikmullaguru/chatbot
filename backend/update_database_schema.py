"""
Database migration script to add missing columns to existing tables.
"""
import sys
from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models import *

def add_missing_columns():
    """
    Add missing columns to the database tables.
    """
    db = SessionLocal()
    
    try:
        # Check if user_sessions table has is_active column
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_sessions' 
            AND column_name = 'is_active'
        """))
        
        is_active_exists = result.fetchone() is not None
        
        if not is_active_exists:
            print("Adding is_active column to user_sessions table...")
            db.execute(text("""
                ALTER TABLE user_sessions 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE
            """))
            print("Added is_active column to user_sessions table.")
        else:
            print("is_active column already exists in user_sessions table.")
        
        # Check if user_sessions table has revoked_at column
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_sessions' 
            AND column_name = 'revoked_at'
        """))
        
        revoked_at_exists = result.fetchone() is not None
        
        if not revoked_at_exists:
            print("Adding revoked_at column to user_sessions table...")
            db.execute(text("""
                ALTER TABLE user_sessions
                ADD COLUMN revoked_at TIMESTAMP
            """))
            print("Added revoked_at column to user_sessions table.")
        else:
            print("revoked_at column already exists in user_sessions table.")
        
        # Check if user_sessions table has created_at column
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'user_sessions'
            AND column_name = 'created_at'
        """))
        
        created_at_exists = result.fetchone() is not None
        
        if not created_at_exists:
            print("Adding created_at column to user_sessions table...")
            db.execute(text("""
                ALTER TABLE user_sessions
                ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            print("Added created_at column to user_sessions table.")
        else:
            print("created_at column already exists in user_sessions table.")
        
        # Commit the changes
        db.commit()
        print("Database schema updated successfully.")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    add_missing_columns()