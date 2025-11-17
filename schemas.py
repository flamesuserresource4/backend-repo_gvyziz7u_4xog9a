"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Class name lowercased = collection name.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr, HttpUrl

# Portfolio item schema (collection: "portfolioitem")
class PortfolioItem(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the work")
    category: Literal[
        "Interiors",
        "Exteriors",
        "Drone / Aerial",
        "Architectural Details",
        "Commercial Spaces",
        "Short-Let & Airbnb",
    ] = Field(..., description="Portfolio category")
    src: HttpUrl = Field(..., description="Public image URL")
    caption: Optional[str] = Field(None, description="Short caption/notes")
    width: Optional[int] = Field(None, ge=1, description="Image width if known")
    height: Optional[int] = Field(None, ge=1, description="Image height if known")

# Contact message schema (collection: "contactmessage")
class ContactMessage(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    message: str = Field(..., min_length=5, max_length=5000)

# Example leftover schemas can remain if needed by admin tools
class User(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=120)
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str
    in_stock: bool = True
