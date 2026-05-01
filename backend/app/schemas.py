from typing import Optional, List
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str
    age: Optional[int]
    gender: Optional[str]
    occupation: Optional[str]
    preferences: Optional[List[str]] = []


class UserUpdate(BaseModel):
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    occupation: Optional[str]
    preferences: Optional[List[str]]


class ItemCreate(BaseModel):
    title: str
    genres: Optional[str] = ""


class ItemUpdate(BaseModel):
    title: Optional[str]
    genres: Optional[str]


class Interaction(BaseModel):
    user_id: int
    item_id: int
    rating: Optional[float] = Field(None, ge=0, le=5)
    liked: Optional[bool] = None
