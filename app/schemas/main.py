from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict
from typing import Optional
from typing_extensions import Literal
from fastapi import Query


Base = declarative_base()

class BaseListRequest(BaseModel):
    search: Optional[str] = None
    limit: Optional[int] = Query(default=10, ge=10, le=5000)
    offset: Optional[int] = Query(default=0, ge=0)
    sort: Optional[str] = 'id'
    order: Optional[Literal['asc', 'desc', '']] = Query(default='desc')

    model_config = ConfigDict(from_attributes=True)
    
class BaseResponseModel(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)

class BaseCSVModel(BaseModel):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
    
class BaseUpdateModel(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)
    
class BaseCreateModel(BaseModel):
    
    model_config = ConfigDict(from_attributes=True)