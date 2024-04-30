import pandas as pd

from fastapi import APIRouter, Depends, Request, File, UploadFile, HTTPException, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


import os


# MYSQL WRITE config
DB_MYSQL_WRITE_HOST = os.getenv("DB_MYSQL_WRITE_HOST")
DB_MYSQL_WRITE_DATABASE = os.getenv("DB_MYSQL_WRITE_DATABASE")
DB_MYSQL_WRITE_USERNAME = os.getenv("DB_MYSQL_WRITE_USERNAME")
DB_MYSQL_WRITE_PASSWORD = os.getenv("DB_MYSQL_WRITE_PASSWORD")
DB_MYSQL_WRITE_PORT = os.getenv("DB_MYSQL_WRITE_PORT")
# MYSQL READ config
DB_MYSQL_READ_HOST = os.getenv("DB_MYSQL_READ_HOST")
DB_MYSQL_READ_DATABASE = os.getenv("DB_MYSQL_READ_DATABASE")
DB_MYSQL_READ_USERNAME = os.getenv("DB_MYSQL_READ_USERNAME")
DB_MYSQL_READ_PASSWORD = os.getenv("DB_MYSQL_READ_PASSWORD")
DB_MYSQL_READ_PORT = os.getenv("DB_MYSQL_READ_PORT")

router = APIRouter()
base = declarative_base()
templates = Jinja2Templates(directory="app/templates")


    
class Product(base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tax_rate = Column(Integer)
    moadian_product_id = Column(String)
    status = Column(Boolean)
    state = Column(Boolean)
    
    def get_table_name(self):
        return self.__tablename__

engine_write = create_engine(
    url = f"mysql://{DB_MYSQL_WRITE_USERNAME}:{DB_MYSQL_WRITE_PASSWORD}@{DB_MYSQL_WRITE_HOST}:{DB_MYSQL_WRITE_PORT}/{DB_MYSQL_WRITE_DATABASE}",
    )
engine_read = create_engine(
    url = f"mysql://{DB_MYSQL_READ_USERNAME}:{DB_MYSQL_READ_PASSWORD}@{DB_MYSQL_READ_HOST}:{DB_MYSQL_READ_PORT}/{DB_MYSQL_READ_DATABASE}",
    )
SessionLocal_write = sessionmaker(autocommit=False, autoflush=False, bind=engine_write)
SessionLocal_read = sessionmaker(autocommit=False, autoflush=False, bind=engine_read)
        
def get_db_write():
    db = SessionLocal_write()
    try:
        yield db
    finally:
        db.close()

def get_db_read():
    db = SessionLocal_read()
    try:
        yield db
    finally:
        db.close()

@router.get("/devops-utils/v1/products/tax-and-moadian/list")
async def get_products(id: int = None, limit: int = Query(default=100, le=100), offset: int = 0 ,db: Session = Depends(get_db_read), request: Request = None):
    try:
        if id:
            products = db.query(Product).filter(Product.status == 0, Product.id == id).limit(limit).offset(offset).all()
        else:
            products = db.query(Product).filter(Product.status == 0).limit(limit).offset(offset).all()
    except Exception as e:
        return HTTPException("500", 'Can not get product list from database: %s' % e)
    products_list = [{'id': p.id, 'name': p.name, 'tax_rate': None if p.tax_rate is None else p.tax_rate, 'moadian_product_id': p.moadian_product_id, "status": "Online" if p.status == 0 else "Offline"} for p in products]
    return products_list

@router.post("/devops-utils/v1/products/tax-and-moadian/import-csv")
async def update_products(file: UploadFile = File(...), db_write: Session = Depends(get_db_write), db_read: Session = Depends(get_db_read)):
    """
    Uploads a CSV file and updates data in the 'products' table based on 'id'.

    Args:
        file (UploadFile): The uploaded CSV file.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        str: Message indicating success or error.
    """
    try:
        updated_products = []
        # Define function to update data (using pandas for efficiency)
        def update_data(dic_chunk):
            for row in dic_chunk:
                if row["tax_rate"] is not None:
                    if row["tax_rate"] > 100 or row["tax_rate"] < 0:
                        return HTTPException(status_code=422, detail="Data problem - id={_id} - tax rate={tax_rate}".format(_id = row["id"], tax_rate = row["tax_rate"]))
                try:
                    product = db_read.query(Product).filter(Product.id == row["id"]).first()
                except:
                    return HTTPException(status_code=404, detail="Product not found - id={_id}".format(_id=row["id"]))
                product.tax_rate = row["tax_rate"]
                product.moadian_product_id = row["moadian_product_id"]
                updated_products.append(product)                    
                
        for chunk in pd.read_csv(file.file, chunksize=1000, iterator=True):
            if "ID" not in chunk.columns or "Tax Rate" not in chunk.columns or "Moadian Product ID" not in chunk.columns :
                return HTTPException(status_code=422, detail=f"Bad CSV file - check csv columns") 
            my_chunck=[]
            try:
                for _, row in chunk.iterrows():
                    if row["Tax Rate"] != row["Tax Rate"]:
                        tax_rate = None
                    else:
                        tax_rate = int(row["Tax Rate"])
                    if row["Moadian Product ID"] != row["Moadian Product ID"]:
                        moadian_product_id = ""
                    else:
                        moadian_product_id = int(row["Moadian Product ID"])
                    my_chunck.append({"id": int(row["ID"]), "tax_rate": tax_rate, "moadian_product_id": moadian_product_id})
            except Exception as e:
                return HTTPException(status_code=422, detail=f"Bad CSV file: {e}")
            update_data(my_chunck)
            
        db_write.execute(text(f"UPDATE {Product().get_table_name()} SET tax_rate = Null, moadian_product_id= \"\";"))
        db_write.bulk_save_objects(updated_products)
        db_write.commit()
        
        return 200, "CSV data successfully processed for updates in 'products' table."

    except Exception as e:
        return HTTPException(status_code=500, detail="Error occurred during update process. Please check the server logs.")