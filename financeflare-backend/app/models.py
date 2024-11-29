from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import date
from app.database import Base

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    description = Column(String, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, index=True)

# Pydantic models for requests and responses
class TransactionBase(BaseModel):
    date: date
    description: str
    amount: float
    category: str

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int

    class Config:
        orm_mode = True

class CategoryRule(Base):
    __tablename__ = "category_rules"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, unique=True, nullable=False)
    category = Column(String, nullable=False)



