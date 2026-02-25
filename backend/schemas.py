from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    """Token response schema for authentication"""
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str
    password: str


class CarResponse(BaseModel):
    """Schema for car response with all fields"""
    id: int
    brand: str
    model: str
    year: int
    price: int
    color: str
    link: str
    
    model_config = ConfigDict(from_attributes=True)
