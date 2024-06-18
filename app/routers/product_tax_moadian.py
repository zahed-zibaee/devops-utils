from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from sqlalchemy import text, or_, and_, func
from sqlalchemy.orm import Session
from datetime import datetime

import pytz
import pandas as pd
import io
import csv

from app.schemas.main import GetProducts, Product
from app.core.logging import logger
from app.core.db import get_db_mysql_write, get_db_mysql_read


router = APIRouter()
 
@router.get("/devops-tools/v1/products/tax_and_moadian/list")
async def get_products(
    params: GetProducts = Depends(),
    db: Session = Depends(get_db_mysql_read)
    ):
    """
    Retrieves a list of products from the database with optional filtering by product ID.

    Args:
        id (int, optional): The ID of the specific product to retrieve.
        limit (int, optional): The maximum number of products to return. Defaults to 100, must be <= 100.
        offset (int, optional): The number of products to skip before starting to collect the result set. Defaults to 0.
        db (Session): A database session dependency for querying the database.

    Returns:
        List[Dict]: A list of products with each product's details.
    """
    
    try:
        total_not_filtered = db.query(func.count(Product.id)).filter(Product.status == 0).scalar()
        if params.search:
            search_filter = and_(
                or_(
                    Product.id == params.search,
                    Product.name.ilike(f"%{params.search}%"),
                ), 
                Product.status == 0
            )
            products = db.query(Product).filter(search_filter).limit(params.limit).offset(params.offset).all()
            total = db.query(func.count(Product.id)).filter(search_filter).scalar()
        else:
            products = db.query(Product).filter(Product.status == 0).limit(params.limit).offset(params.offset).all()
            total = total_not_filtered        
    except Exception as e:
        logger.error('Can not get product list from database: ' + str(e))
        raise HTTPException(status_code=503, detail='Can not get product list from database.')
    products_list = [
        {'id': p.id, 
         'name': p.name, 
         'tax_rate': 'Not Defined' if p.tax_rate is None else p.tax_rate, 
         'moadian_product_id': p.moadian_product_id, 
         "state": "Online" if p.state == 1 else "Offline"
        } for p in products]
    logger.info(f'get product list: {str(products_list[:5])} ...')
    return {"rows": products_list, "total": total, "totalNotFiltered": total_not_filtered}

@router.get("/devops-tools/v1/products/tax_and_moadian/export_csv")
async def get_products(
    db: Session = Depends(get_db_mysql_read)
    ):
    """
    Exports a list of products from the database to a CSV file.

    The products are filtered to include only those with a status of 0 (active).

    Args:
        db (Session): A database session dependency for querying the database.

    Returns:
        Response: A response object containing the CSV file with product details.
    """
    try:
        products = db.query(Product).filter(Product.status == 0).all()       
    except Exception as e:
        logger.error('Can not get product list from database: ' + str(e))
        raise HTTPException(status_code=503, detail='Can not get product list from database.')
    products_list = [
        {'ID': p.id, 
         'Name': p.name, 
         'Tax Rate': 'Not Defined' if p.tax_rate is None else p.tax_rate, 
         'Moadian Product ID': p.moadian_product_id, 
         "State": "Online" if p.state == 1 else "Offline"
        } for p in products]
    logger.info(f'export product csv...')
    tz = pytz.timezone('Asia/Tehran')
    date_time = datetime.now(tz).strftime('%Y%m%d%H%M')
    
    strbuff = io.StringIO()
    products_csv_data = csv.DictWriter(strbuff, fieldnames=["ID", "Name", "Tax Rate", "Moadian Product ID", "State"])
    products_csv_data.writeheader()
    products_csv_data.writerows(products_list)
    
    csv_content = strbuff.getvalue().encode('utf-8-sig')
    strbuff.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=products_tax_and_moadian_{date_time}.csv"}
    )

@router.post("/devops-tools/v1/products/tax_and_moadian/import_csv")
async def update_products(
    file: UploadFile = File(...), 
    db_write: Session = Depends(get_db_mysql_write), 
    db_read: Session = Depends(get_db_mysql_read)
    ):
    """
    Uploads a CSV file and updates data in the 'products' table based on 'id'.

    Args:
        file (UploadFile): The uploaded CSV file.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        str: Message indicating success or error.
    """
    updated_products = []
    # Define function to update data (using pandas for efficiency)
    def update_data(dic_chunk):
        for row in dic_chunk:
            if row["tax_rate"] is not None:
                if row["tax_rate"] > 100 or row["tax_rate"] < 0:
                    raise HTTPException(
                        status_code=422, 
                        detail="Data problem - id={_id} - tax rate={tax_rate}".format(
                            _id = row["id"], 
                            tax_rate = row["tax_rate"]
                        )
                    )
            try:
                product = db_read.query(Product).filter(Product.id == row["id"]).first()
                if not product:
                    raise HTTPException(status_code=404, detail="Product not found - id={_id}".format(_id=row["id"]))
            except:
                    raise HTTPException(status_code=404, detail="Can not get product {_id} from database".format(_id=row["id"]))
            product.tax_rate = row["tax_rate"]
            product.moadian_product_id = row["moadian_product_id"]
            updated_products.append(product)                    
            
    for chunk in pd.read_csv(file.file, chunksize=1000, iterator=True):
        if "ID" not in chunk.columns or "Tax Rate" not in chunk.columns or "Moadian Product ID" not in chunk.columns :
            raise HTTPException(
                status_code=422, 
                detail=f"Bad CSV file - check csv columns"
            ) 
        my_chunck = []
        try:
            for _, row in chunk.iterrows():
                if row["Tax Rate"] == "Not Defined":
                    tax_rate = None
                else:
                    tax_rate = int(float(row["Tax Rate"]))
                if row["Moadian Product ID"] != row["Moadian Product ID"]:
                    moadian_product_id = ""
                else:
                    moadian_product_id = int(float(row["Moadian Product ID"]))
                my_chunck.append(
                    {"id": int(row["ID"]), "tax_rate": tax_rate, "moadian_product_id": moadian_product_id}
                )
        except Exception as e:
            logger.error(f"Bad CSV file: {e}")
            raise HTTPException(status_code=422, detail=f"Bad CSV file.")
        update_data(my_chunck)
    try:   
        db_write.execute(text(
            f"UPDATE {Product().get_table_name()} SET tax_rate = Null, moadian_product_id= \"\";"
            ))
        db_write.bulk_save_objects(updated_products)
        db_write.commit()
    except Exception as e:
        logger.error(f"Can not commit data: {e}")
        raise HTTPException(status_code=503 , detail=f"Can not commit data.")

    return {"detail": "CSV data successfully processed for updates in products table."}

