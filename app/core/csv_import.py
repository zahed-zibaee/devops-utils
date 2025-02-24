from sqlalchemy.orm import Session
from typing import List, Dict, Any, Type, Optional, Generator, Callable
from fastapi import UploadFile, HTTPException, status
from datetime import datetime, timezone
from io import StringIO
import pandas as pd
import json

from app.core.logging import logger
from app.core.redis import lock, unlock, set_cache, get_cache

def set_task_import_csv_status(
    task_id: int, 
    status: str, 
    domain: str, 
    error_msg=None, 
    ttl=600
    ) -> None:
    status_data = {"status": status}
    if error_msg:
        logger.error(error_msg)
        status_data["error"] = error_msg
    set_cache(domain, f"import_csv_{task_id}", json.dumps(status_data), ttl)

def get_task_import_csv_status(task_id: int, domain) -> None:
    try:
        return json.loads(get_cache(domain, f"import_csv_{task_id}"))
    except:
        logger.warning(f"Can not find task import_csv_{task_id}")
        return {"status": "unknown"}   
    
def validate_csv_data(
    df: pd.DataFrame,
    required_columns: List[str],
    csv_model: Type,
    domain: str,
    remove_csv_null_data: Callable[[pd.DataFrame], pd.DataFrame],
    batch_size: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Validates a DataFrame against required columns and a Pydantic model.

    - Ensures required columns exist.
    - Removes rows where all values (except ignored columns) are null.
    - Validates each row using the provided Pydantic model.
    - Stops processing immediately if any row is invalid.
    - Processes in batches for efficiency.

    :param df: Pandas DataFrame containing CSV data.
    :param required_columns: List of required column names.
    :param csv_model: Pydantic model for validation.
    :param task_id: Task ID for tracking.
    :param domain: Domain name (for logging/status updates).
    :param remove_csv_null_data: Function to clean null values in DataFrame.
    :return: List of valid rows as dictionaries.
    :raises ValueError: If any row is invalid.
    """
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        error_msg = f"CSV file for {domain} is missing required columns: {', '.join(missing_columns)}"
        raise ValueError(error_msg)

    remove_csv_null_data(df)

    valid_rows = []
    errors = []
    
    records = df.to_dict(orient="records")

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        for idx, row in enumerate(batch):
            try:
                valid_rows.append(csv_model(**row).model_dump())
            except Exception as e:
                errors.append(f"Row {row} failed validation: {str(e)}")

    if errors:
        error_summary = f"CSV validation failed for {domain}: {len(errors)} errors found. First errors: {
            errors[0][:500]
            .replace("\n", " ")
            .replace("\\n", " ")
            .replace("    For further information visit https://errors.pydantic.dev/", " ")}"
        logger.debug(f"CSV validation failed for {domain}: {len(errors)} errors found. Errors: {errors}") 
        raise ValueError(error_summary)

    logger.debug(f"Total validated rows: {len(valid_rows)}")
    return valid_rows

def process_csv(
    file: UploadFile,
    required_columns: List[str],
    csv_model: Type,
    domain: str,
    remove_csv_null_data: Callable[[pd.DataFrame], pd.DataFrame],
    encoding: str = "utf-8-sig",
) -> List[Dict[str, Any]]:
    """
    Processes a CSV file.
    
    :param file: Uploaded CSV file
    :param task_id: Task ID for tracking
    :param required_columns: List of required CSV columns
    :param csv_model: Pydantic model for validation
    :param domain: Domain name (for logging/status)
    :param remove_csv_null_data: Function to clean CSV null values
    :param encoding: CSV encoding format
    :return: list of validated rows
    """

    csv_data = []
    try:
        file.file.seek(0)
        content = file.file.read().decode(encoding) 
        df = pd.read_csv(StringIO(content)) 
        
        validated_data = validate_csv_data(
            df=df,
            required_columns=required_columns,
            csv_model=csv_model,
            domain=domain,
            remove_csv_null_data=remove_csv_null_data
        )
        csv_data.extend(validated_data)

    except pd.errors.EmptyDataError:
        error_msg = f"CSV file for {domain} is empty"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    except pd.errors.ParserError as e:
        error_msg = f"CSV parsing error for {domain}: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    except Exception as e:
        error_msg = f"Failed to process CSV file for {domain}: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )
    
    logger.debug(f"csv data of {len(csv_data)} rows processed. data: {csv_data[:5]}")        
    return csv_data
    
def validate_foreign_keys(
    rows: List[Dict[str, Any]],
    foreign_data: Dict[str, Dict[str, Any]],
    batch_size: int = 1000,  
) -> None:
    """
    Validate foreign keys using `foreign_data` to minimize database queries.

    :param rows: List of rows (each row is a dictionary of column values)
    :param foreign_data: Dictionary mapping foreign key fields to related models and their metadata.
    :param batch_size: Number of rows to process per batch
    :raises ValueError: If any foreign key is invalid.
    """
    fk_values_map = {fk: set() for fk in foreign_data}
    for row in rows:
        for fk_field, fk_details in foreign_data.items():
            fk_value = row.get(fk_field)
            if fk_value:
                fk_values_map[fk_field].add(fk_value)
                
    for fk_field, fk_details in foreign_data.items():
        related_db: Session = fk_details.get("db")
        related_model = fk_details.get("model")
        related_pk_field = fk_details.get("pk", "id")  

        if not related_db or not related_model:
            raise ValueError(f"Invalid foreign data configuration for {fk_field}")

        fk_values_list = list(fk_values_map[fk_field])
        valid_keys = set()
        
        for i in range(0, len(fk_values_list), batch_size):
            batch = fk_values_list[i : i + batch_size]
            existing_records = (
                related_db.query(getattr(related_model, related_pk_field))
                .filter(getattr(related_model, related_pk_field).in_(batch))
                .all()
            )
            valid_keys.update({getattr(record, related_pk_field) for record in existing_records})

        for row in rows:
            fk_value = row.get(fk_field)
            if fk_value and fk_value not in valid_keys:
                raise ValueError(f"Invalid foreign key: {fk_field}={fk_value} does not exist in {related_model.__tablename__}")

def process_rows(
    db_write: Session,
    csv_rows: List[Dict[str, Any]],
    model: Type,
    domain: str,
    existing_rows_dict: Dict[Any, Any],
    update_row_data: Callable[[Any, Dict[str, Any]], Type],  
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None,
    perform_insert: bool = False,
    perform_update: bool = False,
    perform_delete: bool = False,
    soft_delete_field: str = "deleted_at",
    soft_delete_value: Any = datetime.now(timezone.utc),
    primary_key: str = "id",
) -> None:
    """
    Process a chunk of CSV data and apply inserts, updates, and deletions in a single transaction.

    :param db_write: SQLAlchemy session (write database)
    :param chunk: List of dictionaries representing CSV rows
    :param model: SQLAlchemy model
    :param existing_rows_dict: Dictionary of existing database rows keyed by primary key
    :param foreign_data: Dictionary of foreign key fields mapped to related models
    :param update_row_data: Function of update
    :param perform_insert: If True, insert new rows
    :param perform_update: If True, update existing rows
    :param perform_delete: If True, mark rows as deleted if missing in CSV
    :param soft_delete_field: Field used for soft deletion
    :param soft_delete_value: Value to mark a row as deleted
    :param primary_key: Name of the primary key field
    :raises ValueError: If any error occurs, stops immediately.
    """
    try:
        new_rows = []
        updated_rows = []
        deleted_rows = []
        all_csv_ids = {row[primary_key] for row in csv_rows if primary_key in row}
        
        # Validate foreign keys before processing
        if foreign_data:
            try:
                validate_foreign_keys(csv_rows, foreign_data)  
            except Exception as e:
                raise ValueError(f"Foreign key validation failed: {e}") 

        for csv_row in csv_rows:
            row_id = csv_row.get(primary_key)

            row = existing_rows_dict.get(row_id)

            # Update existing row
            if row and perform_update:
                try:
                    row = update_row_data(row, csv_row)
                    updated_rows.append(row)
                except Exception as e:
                    error_msg = f"Failed to update row {row_id}: {e}"
                    raise ValueError(error_msg)  

            # Insert new row
            elif not row and perform_insert:
                try:
                    new_row = model(**csv_row)
                    new_rows.append(new_row)
                except Exception as e:
                    error_msg = f"Failed to insert row {row_id}: {str(e)}"
                    raise ValueError(error_msg)  
                
        # Handle soft deletions
        if perform_delete:
            deleted_rows = [
                row
                for row_id, row in existing_rows_dict.items()
                if row_id not in all_csv_ids
            ]
            for row in deleted_rows:
                if hasattr(row, soft_delete_field):
                    setattr(row, soft_delete_field, soft_delete_value)

        logger.debug(f"CSV Ready to import: {len(new_rows)} insert row(s), {len(updated_rows)} update row(s), {len(deleted_rows)} delete row(s).")
        # Bulk operations for performance
        if new_rows:
            db_write.bulk_save_objects(new_rows)
        if updated_rows:
            db_write.bulk_save_objects(updated_rows)
        if deleted_rows:
            db_write.bulk_save_objects(deleted_rows)

        db_write.commit()
        logger.info(f"CSV import for {domain} completed: {len(new_rows)} inserted, {len(updated_rows)} updated, {len(deleted_rows)} deleted.")

    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        db_write.rollback()
        raise

def import_to_csv_task(
    csv_rows: Callable,
    task_id: int,
    db_read: Session,
    db_write: Session,
    model: Type,
    domain: str,
    update_row_data: Callable[[Any, Dict[str, Any]], Type],
    truncate_data: Optional[Callable[[Session], None]] = None,
    lock_name: Optional[str] = None,
    soft_delete_condition: Optional[Callable[[Any], bool]] = None,
    perform_insert: bool = False,
    perform_update: bool = False,
    perform_delete: bool = False,
    soft_delete_field: str = "deleted_at",
    soft_delete_value: Any = datetime.now(timezone.utc),
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None,
    primary_key: str = "id",
) -> None:
    """
    Generic function to import CSV data into the database.
    Supports insert, update, and delete operations within a single transaction.

    :param file: Uploaded CSV file
    :param required_columns: List of required CSV columns
    :param csv_model: Pydantic model for validation
    :param task_id: Task ID for tracking
    :param db_read: SQLAlchemy read session
    :param db_write: SQLAlchemy write session
    :param model: SQLAlchemy model for database operations
    :param domain: Domain name (for logging/status)
    :param remove_csv_null_data: Function to clean CSV null values
    :param encoding: CSV encoding format
    :param truncate_data: Function to truncate existing data before import
    :param lock_name: Lock name to prevent concurrent execution
    :param soft_delete_condition: Condition for soft deleting old records
    :param perform_insert: If True, inserts new records
    :param perform_update: If True, updates existing records
    :param perform_delete: If True, soft deletes missing records
    :param soft_delete_field: Column name for soft deletion
    :param soft_delete_value: Value to mark rows as deleted
    :param foreign_data: Dictionary of foreign keys to validate
    :param primary_key: Primary key field name
    """
    # Acquire lock to prevent concurrent execution
    lock_token = lock(lock_name, 1200)
    if not lock_token:
        set_task_import_csv_status(task_id, "failed", domain, f"Operation {lock_name} is already in progress for {domain}.")
        raise ResourceWarning(f"Operation {lock_name} is already in progress for {domain}.")

    try:
        set_task_import_csv_status(task_id, "pending", domain)
        logger.debug(f"Starting CSV import for {domain}")

        if truncate_data:
            truncate_data(db_write)

        query = db_read.query(model)
        if soft_delete_condition is not None:
            query = query.filter(soft_delete_condition)

        existing_rows_dict = {getattr(row, primary_key): row for row in query.all()}
        
        process_rows(
            db_write=db_write,
            csv_rows=csv_rows,
            model=model,
            domain=domain,
            existing_rows_dict=existing_rows_dict,
            foreign_data=foreign_data,
            update_row_data=update_row_data,
            perform_insert=perform_insert,
            perform_update=perform_update,
            perform_delete=perform_delete,
            soft_delete_field=soft_delete_field,
            soft_delete_value=soft_delete_value,
            primary_key=primary_key,
        )

        set_task_import_csv_status(task_id, "succeeded", domain)

    except Exception as e:
        set_task_import_csv_status(task_id, "failed", domain, f"Import CSV failed for {domain}: {str(e)}")
        raise
    
    finally:
        logger.debug(f"Released lock {lock_name} for {domain}")
        unlock(lock_name, lock_token)

