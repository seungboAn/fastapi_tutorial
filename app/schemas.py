# app/schemas.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str

class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

class GenerationHistory(BaseModel):
    id: int
    user_id: int
    image_url: str
    created_at: str

    class Config:
        orm_mode = True