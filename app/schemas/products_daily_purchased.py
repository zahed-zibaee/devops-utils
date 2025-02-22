

from datetime import date, datetime
from pydantic import model_validator, Field
from typing import Optional
from sqlalchemy import Column, Integer, String, Date, BigInteger
from pandas import isna

from app.schemas.main import Base, BaseResponseModel, BaseCSVModel, BaseUpdateModel, BaseCreateModel
       
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
    date: date
    price: int = Field(ge=0, le=9223372036854775806)
    count: int = Field(ge=0, le=9223372036854775806)
    description: Optional[str]
  
class ProductDailyPurchasedCreate(BaseCreateModel):
    product_id: int
    date: date
    price: int = Field(ge=0, le=9223372036854775806)
    count: int = Field(ge=0, le=9223372036854775806)
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
            if isinstance(values["price"], int) and int >= 0 and int <= 9223372036854775806:
                values["price"] = int(values["price"])
            else:
                raise ValueError(f"Invalid data format: price column value must be an integer.")
            if isinstance(values["count"], int) and int >= 0 and int <= 9223372036854775806:
                values["count"] = int(values["count"])
            else:
                raise ValueError(f"Invalid data format: count column value must be an integer.")
            values["date"] = datetime.strptime(values["date"], '%Y-%m-%d')
            if "description" in values and isna(values["description"]):
                values["description"] = ""
            else:
                str(values["description"])

        except (ValueError, KeyError) as e:
            raise ValueError(f"Invalid data format: {e}")
        return values