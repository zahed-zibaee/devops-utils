from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response, BackgroundTasks, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text, or_, and_, func
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

import pytz
import pandas as pd
import io
import csv
import json

from app.schemas.products import GetProducts as ListMainTable,\
    GetProductsResponse as ListMainTableResponse, Product as MainTable, \
    ProductTaxMoadianUpdate  as UpdateByIdRequest, ProductCSVModel as MainTableCSVModel
from app.core.logging import logger
from app.core.db import get_db_postgres_legacy_read, get_db_postgres_legacy_write
from app.core.redis import lock, unlock, is_locked, set_cache, get_cache


router = APIRouter()

DOMAIN = "product"
EXPORT_FILE_PREPEND = "products_tax_and_moadian"
IMPORT_CSV_TASK_SUFFIX = f"{EXPORT_FILE_PREPEND}_csv"
LOCK_IMPORT = IMPORT_CSV_TASK_SUFFIX.upper()
REMOVE_UNWANTED_CSV_FIELD_LIST = ['status']
SOFT_DELETE = MainTable.status == 0

def remove_unwanted_csv_fields(fieldnames):
    return [item for item in fieldnames if item not in REMOVE_UNWANTED_CSV_FIELD_LIST]

REQUIRED_COLUMNS = remove_unwanted_csv_fields([column.name for column in MainTable.__table__.columns])

def update_row_data_csv(product: MainTable, csv_row: dict):
    product.tax_rate = csv_row.get("tax_rate")
    product.moadian_product_id = csv_row.get("moadian_product_id")
  
def drop_csv_null_datas(df: pd.DataFrame):
    df.dropna(subset=[col for col in df.columns if col not in ["id", 'name', 'state']], how="all", inplace=True)
      
def set_task_import_csv_status(task_id, status, error_msg=None, ttl=600):
    status_data = {"status": status}
    if error_msg:
        logger.error(error_msg)
        status_data["error"] = error_msg
    set_cache(DOMAIN, f"{IMPORT_CSV_TASK_SUFFIX}_{task_id}", json.dumps(status_data), ttl)

def get_list_from_db(db: Session, filter_condition=None, limit=None, offset=None, soft_delete=SOFT_DELETE):
    query = db.query(MainTable).filter(soft_delete)

    if filter_condition is not None:
        query = query.filter(filter_condition)
    
    query = query.order_by(MainTable.id.desc())

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    
    return query.yield_per(1000).all()

def remove_tax_and_moadian_product_id_table(db_write):
    db_write.execute(text("UPDATE products SET tax_rate = NULL, moadian_product_id= ''"))

def search_list_tax_and_moadian(params):
    conditions = [SOFT_DELETE]

    if params.search:
        conditions.append(or_(MainTable.id == params.search, MainTable.name.ilike(f"%{params.search}%")))

    return and_(*conditions) 

@router.get("/devops-tools/v1/products/tax_and_moadian/list", response_model=Dict[str, Any])
async def get_list(params: ListMainTable = Depends(), db_read: Session = Depends(get_db_postgres_legacy_read)):
    try:
        total_not_filtered = db_read.query(func.count(MainTable.id)).filter(SOFT_DELETE).scalar()
        search_filter = search_list_tax_and_moadian(params)
        rows = get_list_from_db(db_read, search_filter, params.limit, params.offset)
        total = db_read.query(func.count(MainTable.id)).filter(search_filter).scalar() if params.search else total_not_filtered
        response_data = [ListMainTableResponse.model_validate(row) for row in rows]
        logger.debug(f'Fetched {DOMAIN}: {str(response_data[:5])} ...')
        return {"rows": response_data, "total": total, "totalNotFiltered": total_not_filtered}
    except Exception as e:
        logger.exception(f"Database error while fetching {DOMAIN} list. error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database error while fetching {DOMAIN} list. error: {str(e)}")


@router.get("/devops-tools/v1/products/tax_and_moadian/export_csv", response_class=StreamingResponse)
async def export_csv(
    db: Session = Depends(get_db_postgres_legacy_read)
    ):
    try:
        rows = get_list_from_db(db)
        tz = pytz.timezone('Asia/Tehran')
        date_time = datetime.now(tz).strftime('%Y%m%d%H%M')
        
        strbuff = io.StringIO()
        fieldnames = [column.name for column in MainTable.__table__.columns]
        filtered_fieldnames = remove_unwanted_csv_fields(fieldnames)
        writer = csv.DictWriter(strbuff, fieldnames=filtered_fieldnames)
        writer.writeheader()
        writer.writerows([ListMainTableResponse.model_validate(row).model_dump() for row in rows])
        csv_content = strbuff.getvalue().encode('utf-8-sig')
        strbuff.close()
    
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={EXPORT_FILE_PREPEND}_{date_time}.csv"}
        )
    except Exception as e:
        logger.exception(f"Failed to export {DOMAIN} CSV")
        raise HTTPException(status_code=503, detail=f"Failed to export {DOMAIN} CSV")

def validate_csv_data(df: pd.DataFrame, task_id: int):
    if not set(REQUIRED_COLUMNS).issubset(df.columns):
        set_task_import_csv_status(task_id, "failed", "Bad CSV file: Missing required columns")
        raise ValueError("CSV file is missing required columns")
        
    drop_csv_null_datas(df)

    try:
        return [MainTableCSVModel(**row).model_dump() for row in df.to_dict(orient="records")]
    except Exception as e:
        set_task_import_csv_status(task_id, "failed", f"Data error in CSV file: {e}")
        raise ValueError(f"Data error in CSV file: {e}")

def chunk_csv(file: UploadFile, task_id: int, chunksize: int = 1000) -> List[Dict[str, Any]]:
    try:
        file.file.seek(0)
        logger.debug(f"Processing CSV file: {file.filename}, size: {file.size}")
        
        csv_chunks = []
        for chunk in pd.read_csv(file.file, chunksize=chunksize, encoding="utf-8"):
            logger.debug(f"Processing CSV chunk with {len(chunk)} rows")
            csv_chunks.append(validate_csv_data(chunk, task_id))
        
        return csv_chunks

    except pd.errors.EmptyDataError:
        error_msg = "CSV file is empty"
        logger.error(error_msg)
        set_task_import_csv_status(task_id, "failed", error_msg)
        raise ValueError(error_msg)

    except pd.errors.ParserError as e:
        error_msg = f"CSV parsing error: {str(e)}"
        logger.error(error_msg)
        set_task_import_csv_status(task_id, "failed", error_msg)
        raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"Failed to process CSV file: {str(e)}"
        logger.error(error_msg)
        set_task_import_csv_status(task_id, "failed", error_msg)
        raise ValueError(error_msg)
   
def remove_null_tax_and_moadian_values(chunk):
    return    
def import_csv_task(csv_dic_chunks, task_id: int, db_read: Session, db_write: Session):
    if not db_read or not db_write:
        set_task_import_csv_status(task_id, "failed", "Failed to fetch database sessions. Check the generators.")
        raise RuntimeError("Failed to fetch database sessions. Check the generators.")
    
    def update_data(dic_chunk):
        updated_rows = []
        all_ids = [row["id"] for chunk in csv_dic_chunks for row in chunk]
        db_rows = db_read.query(MainTable).filter(MainTable.id.in_(all_ids)).all()
        db_row_dict = {row.id: row for row in db_rows}

        for csv_row in dic_chunk:
            row = db_row_dict.get(csv_row["id"]) 

            if row is None:  
                error_msg = f"{DOMAIN.capitalize()} not found - id={csv_row['id']}"
                set_task_import_csv_status(task_id, "failed", error_msg)
                continue  

            update_row_data_csv(row, csv_row)
            updated_rows.append(row)

        return updated_rows

    lock_token = lock(LOCK_IMPORT, 1200)
    if not lock_token:
        set_task_import_csv_status(task_id, "failed", f"Operation {LOCK_IMPORT} is already in progress.")
        raise ResourceWarning(f"Operation {LOCK_IMPORT} is already in progress.")
    try:
        set_task_import_csv_status(task_id, 'pending')
        logger.debug(f"Changing {LOCK_IMPORT} lock to {is_locked(LOCK_IMPORT)}")
        
        remove_tax_and_moadian_product_id_table(db_write)
        
        all_updated_rows = []
        for chunk in csv_dic_chunks:
            if chunk:
                all_updated_rows.extend(update_data(chunk))
        
        if all_updated_rows:
            db_write.bulk_save_objects(all_updated_rows)
        db_write.commit()
        set_task_import_csv_status(task_id, 'succeeded')
    except Exception as e:
        set_task_import_csv_status(task_id, "failed", f"Import CSV failed cause: {e}")
        db_write.rollback()
        raise
    finally:
        unlock(LOCK_IMPORT, lock_token)
        logger.debug(f"Changing {LOCK_IMPORT} lock to {is_locked(LOCK_IMPORT)}")


@router.post(
        "/devops-tools/v1/products/tax_and_moadian/import_csv/{task_id}", 
        status_code=status.HTTP_201_CREATED, 
        response_model=Dict[str, Any]
    )
async def import_csc(
    background_tasks: BackgroundTasks,
    task_id: int,
    file: UploadFile = File(...), 
    db_write: Session = Depends(get_db_postgres_legacy_write),
    db_read: Session = Depends(get_db_postgres_legacy_read)
    ):
    set_task_import_csv_status(task_id, 'active', ttl=1260)
    if file.content_type != "text/csv":
        set_task_import_csv_status(task_id, "failed",  "Failed to read CSV file")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Bad Csv file!)."
        )
    if not file.filename.lower().endswith('.csv'):
        set_task_import_csv_status(task_id, "failed",  "Invalid file extension(only csv files!)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid file extension(only csv files!)."
        )
    background_tasks.add_task(
        import_csv_task, 
        chunk_csv(file, task_id, chunksize=1000),
        task_id,
        db_read,
        db_write,
    )
    return JSONResponse(content={'message': 'Task accepted for processing', "task_id": f"{task_id}"}, media_type='application/json')
    
@router.get("/devops-tools/v1/products/tax_and_moadian/import_csv/status/{task_id}", response_model=Dict[str, Any])
async def get_import_csv_task_status(task_id: int):
    try:
        return json.loads(get_cache(DOMAIN, f"{IMPORT_CSV_TASK_SUFFIX}_{task_id}"))
    except:
        logger.warning(f"Can not find task {IMPORT_CSV_TASK_SUFFIX}_{task_id}")
        return {"status": "unknown"}

@router.put("/devops-tools/v1/products/tax_and_moadian/{row_id}", response_model=ListMainTableResponse)
async def update_item(row_id: int, 
        new_data: UpdateByIdRequest,
        db_write: Session = Depends(get_db_postgres_legacy_write)
        ) -> ListMainTableResponse:
    try:
        row = db_write.query(MainTable).filter(MainTable.id == row_id).first()
        if not row:
            logger.error(f"{DOMAIN.capitalize()} not found - id={row['id']}")
            raise HTTPException(status_code=500, detail=f"{DOMAIN.capitalize()} not found - id={row['id']}")

        update_row_data(row, new_data)

        db_write.commit()
        db_write.refresh(row)
        return row
    except Exception as e:
        db_write.rollback()
        logger.exception(f"An error occurred while updating the {DOMAIN}.", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
def update_row_data(row, new_data):
    for key, value in new_data.dict(exclude_unset=True).items():
        setattr(row, key, value)
