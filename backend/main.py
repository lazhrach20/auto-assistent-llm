from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Car
from schemas import Token, CarResponse
from auth import verify_password, create_access_token, get_current_user

# Initialize FastAPI application
app = FastAPI(
    title="Million Miles API",
    description="Backend API for car listings management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Million Miles API is running"}


@app.post("/api/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint for user authentication
    
    Args:
        form_data: OAuth2 form containing username and password
        db: Database session
        
    Returns:
        Token object with access_token and token_type
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Query user by username
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    return Token(access_token=access_token, token_type="bearer")


@app.get("/api/cars", response_model=list[CarResponse])
async def get_cars(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of cars (protected endpoint)
    
    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        List of CarResponse objects
    """
    # Query cars with pagination
    result = await db.execute(
        select(Car)
        .offset(skip)
        .limit(limit)
        .order_by(Car.id.desc())
    )
    cars = result.scalars().all()
    
    return cars
