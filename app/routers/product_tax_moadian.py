from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text, or_, and_
from sqlalchemy.orm import Session
from typing import List, Dict, Any

import pandas as pd
import json

from app.schemas.main import BaseListRequest
from app.core.crud import get_list, update_item
from app.core.csv_export import export_to_csv
from app.core.csv_import import chunk_csv, import_csv_task
from app.schemas.products import ProductTaxMoadianResponseModel, ProductTaxMoadian, \
    ProductTaxMoadianUpdate, ProductTaxMoadianCSVModel
from app.core.logging import logger
from app.core.db import Get_db_postgres_legacy_read, Get_db_postgres_legacy_write
from app.core.redis import set_cache, get_cache

# TOCO
# get all fileds?
# task to db
# srtucture?

router = APIRouter()

MainTableModel = ProductTaxMoadian
GetResponseModel = ProductTaxMoadianResponseModel
UpdateItemModel = ProductTaxMoadianUpdate
CSVModel = ProductTaxMoadianCSVModel
DOMAIN = "product"
EXPORT_FILE_PREPEND = "products_tax_and_moadian"
IMPORT_CSV_TASK_SUFFIX = f"{EXPORT_FILE_PREPEND}_csv"
LOCK_IMPORT_NAME = IMPORT_CSV_TASK_SUFFIX.upper()
REMOVE_UNWANTED_CSV_FIELD_LIST = ['status']
IMPORT_CSV_REQUIRED_COLUMNS = ["id", "tax_rate", "moadian_product_id"]
SOFT_DELETE = MainTableModel.status == 0
DB_SESSION_GENERATOR_READ = Get_db_postgres_legacy_read
DB_SESSION_GENERATOR_WRITE = Get_db_postgres_legacy_write

def update_row_data_csv(main_table: MainTableModel, csv_row: dict):
    main_table.tax_rate = csv_row.get("tax_rate")
    main_table.moadian_product_id = csv_row.get("moadian_product_id")
  
def remove_csv_null_data(df: pd.DataFrame):
    df.dropna(subset=[col for col in df.columns if col not in ["id", 'name', 'state']], how="all", inplace=True)
      
def set_task_import_csv_status(task_id, status, error_msg=None, ttl=600):
    status_data = {"status": status}
    if error_msg:
        logger.error(error_msg)
        status_data["error"] = error_msg
    set_cache(DOMAIN, f"{IMPORT_CSV_TASK_SUFFIX}_{task_id}", json.dumps(status_data), ttl)

@router.get("/devops-tools/v1/products/tax_and_moadian/import_csv/status/{task_id}", response_model=Dict[str, Any])
async def get_task_import_csv_status(task_id: int):
    try:
        return json.loads(get_cache(DOMAIN, f"{IMPORT_CSV_TASK_SUFFIX}_{task_id}"))
    except:
        logger.warning(f"Can not find task {IMPORT_CSV_TASK_SUFFIX}_{task_id}")
        return {"status": "unknown"}   

def truncate_data(db_write):
    db_write.execute(text("UPDATE products SET tax_rate = NULL, moadian_product_id= ''"))

def create_search_filter(params):
    """
    Create a filter condition based on the request parameters.
    """
    conditions = []

    # Add search condition
    if params.search:
        conditions.append(or_(
            MainTableModel.id == params.search,
            MainTableModel.name.ilike(f"%{params.search}%"),
        ))

    # Add additional filter conditions
    # NO FILTER

    # Combine all conditions with AND
    return and_(*conditions) if conditions else None

@router.get("/devops-tools/v1/products/tax_and_moadian/list", response_model=Dict[str, Any])
async def get_product_tax_and_moadian_list(
    params: BaseListRequest = Depends(),
    db: Session = Depends(DB_SESSION_GENERATOR_READ),
):
    # Define search fields for the Product table
    conditions = create_search_filter(params)

    # Call the generic get_list function
    return get_list(
        db=db,
        model=MainTableModel,
        response_schema=GetResponseModel,
        soft_delete_condition=SOFT_DELETE,
        limit=params.limit,
        offset=params.offset,
        conditions=conditions,
    )

@router.get("/devops-tools/v1/products/tax_and_moadian/export_csv", response_class=StreamingResponse)
async def export_product_tax_and_moadian_csv(
    db: Session = Depends(DB_SESSION_GENERATOR_READ),
):
    return export_to_csv(
        db=db,
        model=MainTableModel,
        response_schema=GetResponseModel,
        soft_delete_condition=SOFT_DELETE,
        domain=DOMAIN,
        export_file_prepend=EXPORT_FILE_PREPEND,
        remove_unwanted_fields=REMOVE_UNWANTED_CSV_FIELD_LIST,
    )

@router.post(
    "/devops-tools/v1/products/tax_and_moadian/import_csv/{task_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any],
)
async def import_tax_and_moadian_csv(
    background_tasks: BackgroundTasks,
    task_id: int,
    file: UploadFile = File(...),
    db_write: Session = Depends(DB_SESSION_GENERATOR_WRITE),
    db_read: Session = Depends(DB_SESSION_GENERATOR_READ),
):
    set_task_import_csv_status(task_id, "active", ttl=1260)
    if file.content_type != "text/csv":
        set_task_import_csv_status(task_id, "failed", "Failed to read CSV file")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Bad CSV file!",
        )
    if not file.filename.lower().endswith(".csv"):
        set_task_import_csv_status(task_id, "failed", "Invalid file extension (only CSV files!)")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid file extension (only CSV files!).",
        )

    background_tasks.add_task(
        import_csv_task,
        chunk_csv(
            file=file,
            task_id=task_id,
            required_columns=IMPORT_CSV_REQUIRED_COLUMNS,
            csv_model=ProductTaxMoadianCSVModel,
            domain=DOMAIN,
            set_task_status=set_task_import_csv_status,
            remove_csv_null_data=remove_csv_null_data,
        ),
        task_id=task_id,
        db_read=db_read,
        db_write=db_write,
        model=MainTableModel,
        domain=DOMAIN,
        set_task_status=set_task_import_csv_status,
        update_row_data=update_row_data_csv,
        truncate_data=truncate_data,
        lock_name=LOCK_IMPORT_NAME,
        soft_delete_condition=SOFT_DELETE,
        perform_update=True,
    )

    return JSONResponse(
        content={"message": "Task accepted for processing", "task_id": f"{task_id}"},
        media_type="application/json",
    )

@router.put("/devops-tools/v1/products/tax_and_moadian/{row_id}", response_model=GetResponseModel)
async def update_tax_and_moadian_product(
    row_id: int,
    new_data: UpdateItemModel,
    db: Session = Depends(DB_SESSION_GENERATOR_WRITE),
) -> GetResponseModel:
    return update_item(
        row_id=row_id,
        new_data=new_data,
        db=db,
        model=MainTableModel,
        domain=DOMAIN,
        soft_delete_condition=SOFT_DELETE,
    )