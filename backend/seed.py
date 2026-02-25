import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import select

from database import AsyncSessionLocal
from models import User
from auth import hash_password

# Load environment variables
load_dotenv()


async def seed_database():
    """
    Seed the database with an admin user if it doesn't exist
    """
    # Get admin password from environment or use default
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
    
    print("🌱 Starting database seeding...")
    
    async with AsyncSessionLocal() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("ℹAdmin user already exists. Skipping seed.")
                return
            
            # Create admin user
            print("👤 Creating admin user...")
            hashed_password = hash_password(admin_password)
            admin_user = User(
                username="admin",
                hashed_password=hashed_password
            )
            
            session.add(admin_user)
            await session.commit()
            
            print(f"Admin user created successfully!")
            print(f"   Username: admin")
            print(f"   Password: {admin_password}")
            print("Database seeding completed!")
            
        except Exception as e:
            await session.rollback()
            print(f"Error during seeding: {e}")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
