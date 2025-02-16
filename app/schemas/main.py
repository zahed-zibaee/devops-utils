from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict
from typing import Optional, TypeVar
from fastapi import Query


Base = declarative_base()

class BaseListRequest(BaseModel):
    search: Optional[str] = None
    limit: Optional[int] = Query(default=None, ge=1)
    offset: Optional[int] = Query(default=0, ge=0)

class BaseResponseModel(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)

class BaseCSVModel(BaseModel):
    id: int