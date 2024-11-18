from pydantic import BaseModel, conint, Field
from typing import Optional, List
from fastapi import Query
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ARRAY

from app.core.db import Base

Base = declarative_base()

class GetProducts(BaseModel):
    search: Optional[str] = None
    limit: Optional[int] = Query(default=None, ge=1)
    offset: Optional[int] = Query(default=0, ge=0)
    
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tax_rate = Column(Integer, nullable=True)
    moadian_product_id = Column(String, nullable=False)
    status = Column(Boolean)
    state = Column(Boolean)
    
    def get_table_name(self):
        return self.__tablename__

class ProductUpdate(BaseModel):
    tax_rate: int = Field(None, ge=0, le=100)
    moadian_product_id: str

class ProductUpdateResponse(BaseModel):
    id: int
    name: str
    tax_rate: Optional[int]
    moadian_product_id: str
    
    class Config:
        from_attributes = True
       
class EditOrderLock(BaseModel):
    lock: conint(ge=0, le=10000)

class Job(BaseModel):
    type: str

class Access(Base):
    __tablename__ = 'endpoint_permission'
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, index=True)
    path = Column(String, index=True)
    method = Column(String, index=True)
    permission_ids = Column(ARRAY(Integer))
    public = Column(Boolean, index=True)

class Permissions(Base):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, index=True)
    slug = Column(String, index=True)

class AccessBase(BaseModel):
    slug: str
    path: str
    method: str
    permission_ids: List[int]
    public: bool

    class Config:
        from_attributes = True

class AccessUpdate(BaseModel):
    id: int
    slug: Optional[str]
    path: Optional[str]
    method: Optional[str]
    permission_ids: Optional[List[int]]
    public: Optional[bool]

    class Config:
        from_attributes = True

class PermissionsBase(BaseModel):
    label: str
    slug: str

    class Config:
        from_attributes = True

class PermissionsUpdate(BaseModel):
    id: int
    label: str
    slug: str

    class Config:
        from_attributes = True

class PermissionLabels(BaseModel):
    label: str