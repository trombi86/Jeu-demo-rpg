# models.py
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON
import time

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str

class GameSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, nullable=False, unique=True)
    owner_id: Optional[int] = Field(nullable=True, foreign_key="user.id")
    data: dict = Field(sa_column=Column(JSON), default={})
    updated_at: float = Field(default_factory=lambda: time.time())
