from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Car
from schemas import Token, CarResponse, CarsListResponse
from auth import verify_password, create_access_token, get_current_user

# Initialize FastAPI application
app = FastAPI(
    title="Auto Assistent API",
    description="Backend API for car listings management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Auto Assistent API is running"}


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


@app.get("/api/cars", response_model=CarsListResponse)
async def get_cars(
    cursor: Optional[int] = None,
    limit: int = 20,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of cars with cursor-based pagination and search (protected endpoint)
    
    Args:
        cursor: Cursor (Car ID) for pagination. If None, starts from the beginning
        limit: Maximum number of records to return (default: 20)
        search: Search query to filter by brand, model, or color
        current_user: Authenticated user from JWT token
        db: Database session
        
    Returns:
        CarsListResponse with items, next_cursor, and total count
    """
    # Build base query
    query = select(Car)
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Car.brand.ilike(search_pattern)) |
            (Car.model.ilike(search_pattern)) |
            (Car.color.ilike(search_pattern))
        )
    
    # Apply ordering
    query = query.order_by(Car.id.desc())
    
    # Apply cursor filter if provided
    if cursor is not None:
        query = query.where(Car.id < cursor)
    
    # Add limit
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    cars = result.scalars().all()
    
    # Get total count (with search filter)
    count_query = select(func.count(Car.id))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            (Car.brand.ilike(search_pattern)) |
            (Car.model.ilike(search_pattern)) |
            (Car.color.ilike(search_pattern))
        )
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()
    
    # Determine next cursor
    next_cursor = cars[-1].id if len(cars) == limit else None
    
    return CarsListResponse(
        items=cars,
        next_cursor=next_cursor,
        total=total
    )
