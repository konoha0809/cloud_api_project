from pydantic import BaseModel, Field
from typing import Literal

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=128)

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=4, max_length=128)
    role: Literal["user", "admin"] | None = None   

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: float = Field(..., gt=0)

class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    price: float | None = Field(None, gt=0)

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(default=1, gt=0, le=1000)

class OrderUpdate(BaseModel):
    quantity: int = Field(..., gt=0, le=1000)

class OrderOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    user_id: int
    class Config:
        from_attributes = True