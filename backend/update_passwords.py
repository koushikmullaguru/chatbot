"""
Script to update existing user passwords to hashed passwords
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user_management import User

def update_passwords():
    """
    Update all existing user passwords to hashed passwords
    """
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()
        
        for user in users:
            # Check if password is already hashed (bcrypt hashes start with $2b$)
            if not user.password.startswith('$2b$'):
                # Hash the password
                hashed_password = get_password_hash(user.password)
                user.password = hashed_password
                print(f"Updated password for user: {user.email}")
        
        # Commit the changes
        db.commit()
        print("Password update completed successfully!")
        
    except Exception as e:
        print(f"Error updating passwords: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_passwords()