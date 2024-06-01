from pydantic import BaseModel
from typing import Optional
from fastapi import Query
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class GetProducts(BaseModel):
    search: Optional[str] = None
    limit: Optional[int] = Query(default=None, ge=1)
    offset: Optional[int] = Query(default=0, ge=0)
    
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tax_rate = Column(Integer)
    moadian_product_id = Column(String)
    status = Column(Boolean)
    state = Column(Boolean)
    
    def get_table_name(self):
        return self.__tablename__
