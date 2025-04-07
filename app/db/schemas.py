####################
# Файл schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):  # <- Добавьте этот класс для response_model
    id: int
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True  # Необходимо для работы с ORM

class Token(BaseModel):
    access_token: str
    token_type: str