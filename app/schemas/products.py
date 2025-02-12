from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional
from fastapi import Query
from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from sqlalchemy.orm import relationship
from pandas import isna
from app.schemas.main import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String)
    tax_rate = Column(Integer, nullable=True)
    moadian_product_id = Column(String, nullable=False)
    status = Column(Boolean)
    state = Column(Boolean)
    
    def get_table_name(self):
        return self.__tablename__
    
class GetProducts(BaseModel):
    search: Optional[str] = None
    limit: Optional[int] = Query(default=None, ge=1)
    offset: Optional[int] = Query(default=0, ge=0)

class GetProductsResponse(BaseModel):
    id: int
    name: str
    tax_rate: int | None
    moadian_product_id: str
    state: bool

    model_config = ConfigDict(from_attributes=True)

class ProductTaxMoadianUpdate(BaseModel):
    tax_rate: int = Field(None, ge=0, le=100)
    moadian_product_id: str

    model_config = ConfigDict(from_attributes=True)

class ProductCSVModel(BaseModel):
    id: int
    tax_rate: Optional[int]  
    moadian_product_id: int | str
    
    @model_validator(mode="before")
    def normalize_data(cls, values):
        try:
            values["id"] = int(values["id"])

            if "tax_rate" in values and isna(values["tax_rate"]):
                values["tax_rate"] = None
            else:
                values["tax_rate"] = int(values["tax_rate"]) if values["tax_rate"] is not None else None

            if "moadian_product_id" in values and isna(values["moadian_product_id"]):
                values["moadian_product_id"] = ""
            else:
                values["moadian_product_id"] = int(values["moadian_product_id"])

        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid data format: {e}")
        return values
    
    @field_validator("tax_rate", mode="before")
    def validate_tax_rate(cls, value):
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Invalid tax rate: must be between 0 and 100")
        return value

    @field_validator("moadian_product_id", mode="before")
    def validate_moadian_product_id(cls, value):
        if value in [None, "nan", ""]:
            return ""  
        return str(value)  
