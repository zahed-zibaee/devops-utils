from sqlalchemy.orm import Session
from typing import List, Dict, Any, Type, Optional, Generator, Callable
from fastapi import UploadFile
from datetime import datetime, timezone
import tempfile
import pandas as pd
import os

from app.core.logging import logger
from app.core.redis import lock, unlock
    
def remove_csv_null_data(df):
    pass

def validate_csv_data(
    df: pd.DataFrame,
    required_columns: List[str],
    csv_model: Type,
    task_id: int,
    domain: str,
    set_task_status: Callable[[int, str, str], None],
    remove_csv_null_data: Callable[[pd.DataFrame], None] = remove_csv_null_data
):
    """
    Generic function to validate CSV data.
    """
    # Check if all required columns are present
    if not set(required_columns).issubset(df.columns):
        set_task_status(task_id, "failed", f"Bad CSV file for {domain}: Missing required columns")
        raise ValueError(f"CSV file for {domain} is missing required columns")

    # Remove rows where all values (except ignored columns) are null
    remove_csv_null_data(df)

    try:
        # Validate each row using the provided Pydantic model
        return [csv_model(**row).model_dump() for row in df.to_dict(orient="records")]
    except Exception as e:
        set_task_status(task_id, "failed", f"Data error in CSV file for {domain}: {str(e)}")
        raise ValueError(f"Data error in CSV file for {domain}: {str(e)}")

def chunk_csv(
    file: UploadFile,
    task_id: int,
    required_columns: List[str],
    csv_model: Type,
    domain: str,
    set_task_status: Callable[[int, str, str], None],
    remove_csv_null_data: Callable[[pd.DataFrame], None] = remove_csv_null_data,
    chunksize: int = 1000,
    encoding: str = "utf-8",
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Processes a CSV file in chunks using a temporary file stored on disk.
    This prevents large files from being fully loaded into memory.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="wb", delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Write uploaded file content to temp file
            for chunk in iter(lambda: file.file.read(1024 * 1024), b""):
                temp_file.write(chunk)
    except Exception as e:
        error_msg = f"Failed save CSV file for {domain}: {str(e)}"
        set_task_status(task_id, "failed", error_msg)
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise ValueError(error_msg)
    
    try:
        csv_chunks = []
        with open(temp_path, "r", encoding=encoding) as csv_file:
            for chunk in pd.read_csv(csv_file, chunksize=chunksize):
                validated_chunk = validate_csv_data(
                    df=chunk,
                    required_columns=required_columns,
                    csv_model=csv_model,
                    task_id=task_id,
                    domain=domain,
                    set_task_status=set_task_status,
                    remove_csv_null_data=remove_csv_null_data
                )
                csv_chunks.append(validated_chunk)
                
    except pd.errors.EmptyDataError:
        error_msg = f"CSV file for {domain} is empty"
        set_task_status(task_id, "failed", error_msg)
        raise ValueError(error_msg)

    except pd.errors.ParserError as e:
        error_msg = f"CSV parsing error for {domain}: {str(e)}"
        set_task_status(task_id, "failed", error_msg)
        raise ValueError(error_msg)

    except Exception as e:
        error_msg = f"Failed to process CSV file for {domain}: {str(e)}"
        set_task_status(task_id, "failed", error_msg)
        raise ValueError(error_msg)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return csv_chunks
    
def import_csv_task(
    csv_dic_chunks: List[List[Dict[str, Any]]],
    task_id: int,
    db_read: Session,
    db_write: Session,
    model: Type, 
    domain: str,
    set_task_status: callable,
    update_row_data: callable, 
    truncate_data: Optional[callable] = None,  
    lock_name: Optional[str] = None, 
    soft_delete_condition: Optional[Any] = None,
    perform_insert: bool = False,
    perform_update: bool = False,  
    perform_delete: bool = False,
    soft_delete_field: str = 'deleted_at',
    soft_delete_value: str = datetime.now(timezone.utc),
):
    """
    Generic function to import CSV data into the database.
    Supports insert, update, and delete operations.
    """
    # Acquire lock
    lock_token = lock(lock_name, 1200)
    if not lock_token:
        set_task_status(task_id, "failed", f"Operation {lock_name} is already in progress for {domain}.")
        raise ResourceWarning(f"Operation {lock_name} is already in progress for {domain}.")

    try:
        set_task_status(task_id, "pending")
        logger.debug(f"Starting CSV import for {domain}")

        # Truncate data if required
        if truncate_data:
            truncate_data(db_write)

        # Collect all IDs from the CSV
        all_csv_ids = {row["id"] for chunk in csv_dic_chunks for row in chunk}

        # Fetch existing rows from the database
        existing_rows = db_read.query(model).filter(soft_delete_condition).all() if soft_delete_condition else db_read.query(model).all()
        existing_rows_dict = {row.id: row for row in existing_rows}

        # Perform insert, update, or delete operations
        updated_rows = []
        new_rows = []
        deleted_rows = []

        for chunk in csv_dic_chunks:
            for csv_row in chunk:
                row = existing_rows_dict.get(csv_row["id"])

                # Update existing row
                if row and perform_update:
                    update_row_data(row, csv_row)
                    updated_rows.append(row)

                # Insert new row
                elif not row and perform_insert:
                    new_row = model(**csv_row)
                    new_rows.append(new_row)

        # Delete rows not present in the CSV
        if perform_delete:
            for row_id, row in existing_rows_dict.items():
                if row_id not in all_csv_ids and (not soft_delete_condition or soft_delete_condition(row)):
                    if hasattr(model, soft_delete_field):
                        setattr(row, soft_delete_field, soft_delete_value)
                        updated_rows.append(row)
                    else:
                        raise RuntimeError(f"{domain} do not has soft delete field named '{soft_delete_field}'!")

        # Save changes to the database
        if updated_rows:
            db_write.bulk_save_objects(updated_rows)
        if new_rows:
            db_write.bulk_save_objects(new_rows)
        if deleted_rows:
            db_write.bulk_save_objects(deleted_rows)

        db_write.commit()
        set_task_status(task_id, "succeeded")
        logger.info(f"CSV import for {domain} completed successfully")

    except Exception as e:
        set_task_status(task_id, "failed", f"Import CSV failed for {domain}: {str(e)}")
        db_write.rollback()
        raise
    finally:
        # Release lock if acquired
        if lock_token:
            unlock(lock_name, lock_token)
            logger.debug(f"Released lock {lock_name} for {domain}")