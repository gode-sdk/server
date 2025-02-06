from pydantic import BaseModel
from typing import Optional

# ModDeveloper model
class ModDeveloper(BaseModel):
    id: int
    username: str
    display_name: str
    is_owner: bool

    class Config:
        orm_mode = True  # To enable pydantic model compatibility with ORM models


# Developer model (with SQLAlchemy integration)
from sqlalchemy import Column, Integer, String, Boolean, BigInteger

class Developer(BaseModel):
    id: int
    username: str
    display_name: str
    verified: bool
    admin: bool
    github_id: int

    class Config:
        orm_mode = True  # For ORM compatibility (if using SQLAlchemy)

# SQLAlchemy Model for Developer (if you need to map this to a database)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DeveloperDB(Base):
    __tablename__ = 'developers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)
    github_id = Column(BigInteger, nullable=False)

    def __repr__(self):
        return f"<Developer(id={self.id}, username={self.username}, display_name={self.display_name})>"
