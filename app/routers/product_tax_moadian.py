from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy import text, or_, and_, func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

import pytz
import pandas as pd
import io
import csv
import json

from app.schemas.main import GetProducts, Product
from app.core.logging import logger
from app.core.db import get_db_mysql_write, get_db_mysql_read
from app.core.redis import lock, unlock, is_locked, set_cache, get_cache


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

def csv_file_validator(file: UploadFile, task_id: int, chunksize: int = 1000) -> List[Dict[str, Any]]:
    csv_dic_chunks = []
    try:
        content = file.file.read()
        csv_file = pd.read_csv(io.BytesIO(content), chunksize=chunksize, iterator=True).__next__()
    except Exception as e:
        logger.error("Failed to read CSV file: {}".format(e))
        set_cache(
            "product", 
            f"import_tax_and_moadian_csv_{task_id}", 
            json.dumps(
                {"status": "failed", 
                 "error": "Failed to read CSV file",}
                ), 
            600)
        raise ValueError("Failed to read CSV file")

    required_columns = {"ID", "Tax Rate", "Moadian Product ID"}
    if not required_columns.issubset(csv_file.columns):
        logger.error("Bad CSV file: Data columns problem - columns must be 'ID', 'Tax Rate', 'Moadian Product ID'")
        set_cache(
            "product", 
            f"import_tax_and_moadian_csv_{task_id}", 
            json.dumps(
                {"status": "failed", 
                 "error": "CSV file is missing required columns",}
                ), 
            600)
        raise ValueError("CSV file is missing required columns")

    for chunk in pd.read_csv(io.BytesIO(content), chunksize=chunksize, iterator=True):
        csv_dic = []
        for _, row in chunk.iterrows():
            try:
                product_id = int(row["ID"])
                
                moadian_product_id = int(float(row["Moadian Product ID"])) if pd.notna(row["Moadian Product ID"]) else ""

                if row["Tax Rate"] == "Not Defined":
                    if moadian_product_id == "":
                        continue
                    tax_rate = None
                else:
                    tax_rate = int(float(row["Tax Rate"]))
                    if tax_rate > 100 or tax_rate < 0:
                        logger.error(f"Bad CSV file: Data tax_rate problem - id={product_id}, tax rate={tax_rate}")
                        set_cache(
                            "product", 
                            f"import_tax_and_moadian_csv_{task_id}", 
                            json.dumps(
                                {"status": "failed", 
                                "error": f"Bad CSV file: Data tax_rate problem - id={product_id}, tax rate={tax_rate}",}
                                ), 
                            600)
                        raise ValueError("Invalid tax rate")

            except Exception as e:
                logger.error(f"Bad CSV file: Data problem - id={product_id}, tax rate={row['Tax Rate']}, moadian_product_id={row['Moadian Product ID']}")
                set_cache(
                    "product", 
                    f"import_tax_and_moadian_csv_{task_id}", 
                    json.dumps(
                        {"status": "failed", 
                        "error": f"Bad CSV file: Data problem - id={product_id}, tax rate={row['Tax Rate']}, moadian_product_id={row['Moadian Product ID']}"}
                        ), 
                    600)
                raise ValueError(f"Data error in CSV file: {e}")

            csv_dic.append({
                "id": product_id, 
                "tax_rate": tax_rate, 
                "moadian_product_id": moadian_product_id
            })

        csv_dic_chunks.append(csv_dic)
        
    logger.info(f"csv file is ok with value: {csv_dic_chunks[0][:3]}...")
    return csv_dic_chunks
    
def import_csv_product_tax_and_moadian(
    csv_dic_chunks,
    task_id: int,
    db_write = next(get_db_mysql_write()), 
    db_read = next(get_db_mysql_read())
    ):
    def update_data(dic_chunk):
        updated_products = []
        for row in dic_chunk:
            try:
                product = db_read.query(Product).filter(Product.id == row["id"]).first()
                if not product:
                    logger.error("Product not found - id={_id}".format(_id=row["id"]))
                    set_cache(
                        "product", 
                        f"import_tax_and_moadian_csv_{task_id}", 
                        json.dumps(
                            {"status": "failed", 
                            "error": "Product not found - id={_id}".format(_id=row["id"])}
                            ), 
                        600)
                    raise RuntimeError("Product not found - id={_id}".format(_id=row["id"]))
            except:
                    logger.error("Can not get product {_id} from database".format(_id=row["id"]))
                    set_cache(
                        "product", 
                        f"import_tax_and_moadian_csv_{task_id}", 
                        json.dumps(
                            {"status": "failed", 
                            "error": "Can not get product {_id} from database".format(_id=row["id"])}
                            ), 
                        600)
                    raise RuntimeError("Can not get product {_id} from database".format(_id=row["id"]))
            product.tax_rate = row["tax_rate"] 
            product.moadian_product_id = row["moadian_product_id"]
            updated_products.append(product)
        return updated_products
    
    if not is_locked("PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV"):
        try:
            lock("PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV", 1200)
            set_cache("product", f"import_tax_and_moadian_csv_{task_id}", json.dumps({"status": "pending"}), 600)
            logger.info(f"Changing PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV lock to {is_locked('PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV')}")
            db_write.execute(text(
                f"UPDATE {Product().get_table_name()} SET tax_rate = Null, moadian_product_id= \"\";"
                )
            )
            for chunk in csv_dic_chunks:
                if len(chunk) != 0:
                    db_write.bulk_save_objects(update_data(chunk))
            db_write.commit() 
            set_cache("product", f"import_tax_and_moadian_csv_{task_id}", json.dumps({"status": "succeeded"}), 600)
        except Exception as e:
            logger.info(f"Import CSV file tax and moadian failed cause: {e}")
            set_cache(
            "product", 
            f"import_tax_and_moadian_csv_{task_id}", 
            json.dumps(
                {"status": "failed", 
                "error": f"Import CSV file tax and moadian failed cause: {e}"}
                ), 
            600)  
            db_write.rollback()
            set_cache("product", "import_tax_and_moadian_csv", "failed", 600)
            raise
        finally:
            unlock("PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV")
            logger.info(f"Changing PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV lock to {is_locked('PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV')}")
    else:
        logger.warning(f"Failed changing PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV lock. task already in progress.")
        set_cache(
            "product", 
            f"import_tax_and_moadian_csv_{task_id}", 
            json.dumps(
                {"status": "failed", 
                "error": "Operation PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV is already in progress."}
                ), 
            600)
        raise ResourceWarning("Operation PRODUCT_TAX_AND_MOARDIAN_IMPORT_CSV is already in progress.")

@router.post("/devops-tools/v1/products/tax_and_moadian/import_csv/{task_id}", status_code=status.HTTP_201_CREATED)
async def update_products(
    background_tasks: BackgroundTasks,
    task_id: int,
    file: UploadFile = File(...), 
    ):
    """
    Uploads a CSV file and updates data in the 'products' table based on 'id'.

    Args:
        file (UploadFile): The uploaded CSV file.
        db (Session): SQLAlchemy session for database interaction.

    Returns:
        str: Message indicating success or error.
    """
    set_cache("product", f"import_tax_and_moadian_csv_{task_id}", json.dumps({"status": "active"}), 1260)
    csv_dic_chunks = csv_file_validator(file, task_id, chunksize=1000)
    background_tasks.add_task(
        import_csv_product_tax_and_moadian, 
        csv_dic_chunks,
        task_id
    )
    return JSONResponse(content={'message': 'Task accepted for processing', "task_id": f"{task_id}"}, media_type='application/json')
    
@router.get("/devops-tools/v1/products/tax_and_moadian/import_csv/status/{task_id}")
async def update_products_status(task_id: int):
    try:
        task_status_json = get_cache("product", f"import_tax_and_moadian_csv_{task_id}")
        task_status = json.loads(task_status_json)
        return task_status
    except:
        logger.warning(f"Can not find task import csv tax_and_moadian with id {task_id}")
        return {"status": "unknown"}

