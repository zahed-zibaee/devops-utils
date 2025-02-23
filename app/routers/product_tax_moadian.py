from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text, or_, and_
from sqlalchemy.orm import Session
from typing import Dict, Any

import pandas as pd

from app.schemas.main import BaseListRequest
from app.core.crud import get_list, update_item
from app.core.csv_export import export_to_csv
from app.core.csv_import import import_to_csv_task, process_csv, get_task_import_csv_status, set_task_import_csv_status
from app.schemas.products import ProductTaxMoadianResponseModel, Product, \
    ProductTaxMoadianUpdate, ProductTaxMoadianCSVModel
from app.core.db import get_db_postgres_write, get_db_postgres_read

# TOCO
# task to db
# srtucture?

router = APIRouter()

MainTableModel = Product
GetResponseModel = ProductTaxMoadianResponseModel
UpdateItemModel = ProductTaxMoadianUpdate
CSVModel = ProductTaxMoadianCSVModel
DOMAIN = "product"
SUB_DOMAIN = "products_tax_and_moadian"
LOCK_IMPORT_NAME = f"{SUB_DOMAIN}_csv".upper()
REMOVE_UNWANTED_CSV_FIELD_LIST = ['status']
IMPORT_CSV_REQUIRED_COLUMNS = ["id", "tax_rate", "moadian_product_id"]
SOFT_DELETE = MainTableModel.status == 0
LIST_OPTIONS = None
FOREIGN_KEYS = None
FOREIGN_DATA = None
DB_SESSION_GENERATOR_READ = lambda: next(get_db_postgres_read('legacy'))
DB_SESSION_GENERATOR_WRITE = lambda: next(get_db_postgres_write('legacy'))

def update_row_data(main_table: MainTableModel, csv_row: dict):
    main_table.tax_rate = csv_row.get("tax_rate")
    main_table.moadian_product_id = csv_row.get("moadian_product_id")
    
    return main_table
  
def remove_csv_null_data(df: pd.DataFrame):
    df.dropna(subset=[col for col in df.columns if col not in ["id", 'name', 'state']], how="all", inplace=True)

@router.get(
    "/devops-tools/v1/products/tax_and_moadian/import_csv/status/{task_id}", 
    response_model=Dict[str, Any],
)
async def get_task_import_products_tax_and_moadian_csv_status(task_id: int):
    return get_task_import_csv_status(task_id, SUB_DOMAIN) 

def truncate_data(db_write):
    db_write.execute(text("UPDATE products SET tax_rate = NULL, moadian_product_id= ''"))

def create_search_filter(params):
    """
    Create a filter condition based on the request parameters.
    """
    conditions = []

    # Add search condition
    if params.search:
        try:
            conditions.append(or_(
                MainTableModel.id == int(params.search),
                MainTableModel.name.ilike(f"%{params.search}%"),
            ))
        except:
            conditions.append(
                MainTableModel.name.ilike(f"%{params.search}%"),
            )

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
        sort_field=params.sort if hasattr(params, 'sort') and params.order != "" else 'id',
        sort_order_ascending=True if hasattr(params, 'order') and params.order == "asc" else False,
        options=LIST_OPTIONS,
        foreign_data=FOREIGN_DATA,
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
        domain=SUB_DOMAIN,
        sort_field='id',
        export_file_prepend=SUB_DOMAIN+"_export",
        remove_unwanted_fields=REMOVE_UNWANTED_CSV_FIELD_LIST,
        options=LIST_OPTIONS,
        foreign_data=FOREIGN_DATA,
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
    if file.content_type != "text/csv":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Bad CSV file!",
        )
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid file extension (only CSV files!).",
        )
    set_task_import_csv_status(task_id, "active", SUB_DOMAIN, ttl=1260)
    background_tasks.add_task(
        import_to_csv_task,
        process_csv(
            file=file,
            required_columns=IMPORT_CSV_REQUIRED_COLUMNS,
            csv_model=CSVModel,
            domain=SUB_DOMAIN,
            remove_csv_null_data=remove_csv_null_data,
        ),
        domain=SUB_DOMAIN,
        task_id=task_id,
        db_read=db_read,
        db_write=db_write,
        model=MainTableModel,
        update_row_data=update_row_data,
        truncate_data=truncate_data,
        lock_name=LOCK_IMPORT_NAME,
        soft_delete_condition=SOFT_DELETE,
        perform_update=True,
        foreign_data=FOREIGN_DATA,
        primary_key="id",
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
        response_schema=GetResponseModel,
        soft_delete_condition=SOFT_DELETE,
        foreign_data=FOREIGN_KEYS,
    )