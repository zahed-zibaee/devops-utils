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
    moadian_product_id = Column(String, nullable=False)
    status = Column(Boolean)
    state = Column(Boolean)

class ProductTaxMoadianResponseModel(BaseResponseModel):
    name: str
    tax_rate: Optional[int] = Field(None, ge=0, le=100)
    moadian_product_id: str
    state: bool

    @field_validator("tax_rate")
    def validate_tax_rate(cls, value):
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Tax rate must be between 0 and 100")
        return value
    
    @field_validator("moadian_product_id")
    def validate_moadian_product_id(cls, value):
        if value != "":
            try:
                return str(int(value))
            except:
                return ValueError("Moadian Product ID must be empty string or a number")
        else:
            return ""
    
class ProductTaxMoadianUpdate(BaseUpdateModel):
    tax_rate: Optional[int] = Field(None, ge=0, le=100)
    moadian_product_id: str

class ProductTaxMoadianCSVModel(BaseCSVModel):
    tax_rate: Optional[int]  
    moadian_product_id: str
    
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
                values["moadian_product_id"] = str(int(values["moadian_product_id"]))

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
        if isna(value):
            return ""  
        return str(value)  
