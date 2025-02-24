

from datetime import date, datetime
from pydantic import model_validator, Field, field_validator
from typing import Optional, Union
from sqlalchemy import Column, Integer, String, Date, BigInteger
from pandas import isna

from app.schemas.main import Base, BaseResponseModel, BaseCSVModel, BaseUpdateModel, BaseCreateModel, parse_date
       
class ProductDailyPurchased(Base):
    __tablename__ = "products_daily_purchased"

    id = Column(BigInteger, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    date = Column(Date, nullable=False, index=True)
    price = Column(BigInteger, nullable=False)
    count = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
  
class ProductResponse(BaseResponseModel):
    name: str
   
class ProductDailyPurchasedResponse(BaseResponseModel):
    id: int
    product_id: int
    product_name: str
    date: date
    price: int = Field(ge=0, le=9223372036854775806)
    count: int = Field(ge=0, le=9223372036854775806)
    description: str
    
    @classmethod
    def from_orm(cls, obj):
        
        return cls(
            id=obj.id,
            product_id=obj.products['id'],
            product_name=obj.products['name'],
            date=obj.date,
            price=obj.price,
            count=obj.count,
            description=obj.description,
        )
     
class ProductDailyPurchasedUpdate(BaseUpdateModel):
    product_id: int
    date: Union[str, date]
    price: int = Field(ge=0, le=9223372036854775806)
    count: int = Field(ge=0, le=9223372036854775806)
    description: Optional[str]
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value):
        return parse_date(value)
  
class ProductDailyPurchasedCreate(BaseCreateModel):
    product_id: int
    date: Union[str, date]
    price: int = Field(ge=0, le=9223372036854775806)
    count: int = Field(ge=0, le=9223372036854775806)
    description: Optional[str]
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value):
        return parse_date(value)
          
class ProductDailyPurchasedCSVModel(BaseCSVModel):
    id: Optional[int]
    product_id: int
    date: date
    price: int
    count: int
    description: Optional[str] = ""
    
    @model_validator(mode="before")
    def normalize_data(cls, values):
        try:
            if "id" in values:
                if isna(values["id"]):
                    values["id"] = None
                elif isinstance(values["id"], (int, float)):
                    values["id"] = int(values["id"])
                else:
                    raise ValueError(f'Invalid data format for column id {values["id"]}')
            price = values.get("price", None)
            if isinstance(price, (int, float)) and 0 <= int(price) <= 9223372036854775806:
                values["price"] = int(price)
            else:
                raise ValueError(f"Invalid data format: price column value must be a positive integer. price is {price}")
            count = values.get("count", None)
            if isinstance(count, (int, float)) and 0 <= int(count) <= 9223372036854775806:
                values["price"] = int(price)
            else:
                raise ValueError(f"Invalid data format: count column value must be a positive integer. count is {count}")
            values["date"] = parse_date(values["date"])             
            if "description" in values: 
                if isna(values["description"]):
                    values["description"] = ""
                else:
                    values["description"] = str(values["description"])
            else: 
                raise ValueError(f"Invalid description format: {values.get('description'), None}. Description must be an string.")

        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid data format: {e}")
        return values
