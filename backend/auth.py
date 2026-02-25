import os
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User

# Load environment variables
load_dotenv()

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def hash_password(password: str) -> str:
    """Hash a plain text password"""
    # Bcrypt has a 72 byte limit, encode and truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password"""
    # Bcrypt has a 72 byte limit, encode and truncate if necessary
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token as a string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User object if authentication is successful
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Query user from database
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user
