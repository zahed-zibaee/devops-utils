from pydantic import Field, field_validator, model_validator
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from pandas import isna
from app.schemas.main import Base, BaseResponseModel, BaseCSVModel, BaseUpdateModel


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String)
    tax_rate = Column(Integer, nullable=True)
    moadian_product_id = Column(String, nullable=True)
    status = Column(Boolean)
    state = Column(Boolean)

class ProductTaxMoadianResponseModel(BaseResponseModel):
    name: str
    tax_rate: Optional[int] = Field(None, ge=0, le=100)
    moadian_product_id: str
    state: bool 
    
    @classmethod
    def from_orm(cls, obj):
            
        return cls(
            id=obj.id,
            name=obj.name,
            tax_rate=obj.tax_rate,
            moadian_product_id="" if obj.moadian_product_id == "" or obj.moadian_product_id is None else obj.moadian_product_id,
            state=obj.state,
        )
    
class ProductTaxMoadianUpdate(BaseUpdateModel):
    tax_rate: Optional[int] = Field(None, ge=0, le=100)
    moadian_product_id: str
    
    @field_validator("moadian_product_id", mode="before")
    @classmethod
    def validate_moadian_product_id(cls, value):
        if value != "" and value is not None:
            try:
                return str(int(value))
            except:
                return ValueError(f"Moadian Product ID must be empty string or a number but it got {value}")
        else:
            return ""

class ProductTaxMoadianCSVModel(BaseCSVModel):
    tax_rate: Optional[int] = Field(None, ge=0, le=100) 
    moadian_product_id: str
    
    @model_validator(mode="before")
    def normalize_data(cls, values):
        try:
            if "id" not in values or not isinstance(values["id"], (int, float)):
                raise ValueError(f"Invalid id format: {values.get('id'), None}. ID must be an integer.")
            else:
                values["id"] = int(values["id"])
            if "tax_rate" in values:
                if isna(values["tax_rate"]):
                    values["tax_rate"] = None
                else:
                    try:
                        values["tax_rate"] = int(values["tax_rate"])
                    except:
                        raise ValueError(f'Invalid data format for tax_rate: {values["tax_rate"]}')
            if "moadian_product_id" in values:
                if isna(values["moadian_product_id"]):
                    values["moadian_product_id"] = ""
                else:
                    try:
                        values["moadian_product_id"] = str(int(float(values["moadian_product_id"])))
                    except:
                        raise ValueError(f'Invalid data format for moadian_product_id: {values["moadian_product_id"]}')

        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid data format: {e}")
        return values


