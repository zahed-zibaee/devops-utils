

from datetime import date, datetime
from pydantic import model_validator
from typing import Optional
from sqlalchemy import Column, Integer, String, Date, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from pandas import isna

from app.schemas.main import Base, BaseResponseModel, BaseCSVModel, BaseUpdateModel
from app.schemas.products import Product
       
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
    price: int
    count: int
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
    date: date
    price: int
    count: int
    description: Optional[str]
        
class ProductDailyPurchasedCSVModel(BaseCSVModel):
    product_id: int
    date: date
    price: int
    count: int
    description: Optional[str]
    
    @model_validator(mode="before")
    def normalize_data(cls, values):
        try:
            values["id"] = int(values["id"])
            values["price"] = int(values["price"])
            values["count"] = int(values["count"])
            values["date"] = datetime.strptime(values["date"], '%Y-%m-%d')
            if "description" in values and isna(values["description"]):
                values["description"] = ""
            else:
                str(values["description"])

        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid data format: {e}")
        return values