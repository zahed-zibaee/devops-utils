from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, ARRAY

from app.schemas.main import Base

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