# app/core/crud.py
from typing import List, Dict, Any, Type, Optional, Tuple

from sqlalchemy.orm import Session, load_only
from sqlalchemy.orm.interfaces import ORMOption 
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, select
from fastapi import HTTPException

from app.core.logging import logger

def apply_filters(
    query: Any,
    soft_delete_condition: Optional[Any] = None,
    conditions: Optional[Any] = None,
) -> Any:
    """
    Applies filtering conditions to a SQLAlchemy query.

    Args:
        db (Session): SQLAlchemy database session.
        model (Type): SQLAlchemy model.
        soft_delete_condition (Optional[Any]): Condition to filter soft-deleted rows.
        conditions (Optional[Any]): Additional conditions to apply to the query.
        options (Optional[List[Any]]): ORM options like `joinedload`.

    Returns:
        Any: Query object with applied filters.
    """
    try:
        if soft_delete_condition is not None:
            query = query.filter(soft_delete_condition)

        if conditions is not None:
            query = query.filter(conditions)

        return query

    except SQLAlchemyError as e:
        logger.error(f"Error applying filters: {e}")
        raise


def apply_sorting(
    query: Any,
    model: Type,
    sort_field: Optional[str] = None,
    sort_order_ascending: bool = False,
) -> Any:
    """
    Applies sorting to a SQLAlchemy query.

    Args:
        query (Any): SQLAlchemy query object.
        model (Type): SQLAlchemy model.
        sort_field (Optional[str]): Field to sort by.
        sort_order_ascending (bool): Sort in ascending order if True, otherwise descending.

    Returns:
        Any: Query object with applied sorting.
    """
    try:
        if sort_field:
            if sort_field not in model.__table__.columns.keys():
                raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort_field}")
            column = getattr(model, sort_field)
            query = query.order_by(column.asc() if sort_order_ascending else column.desc())

        return query

    except SQLAlchemyError as e:
        logger.error(f"Error applying sorting: {e}")
        raise


def apply_pagination(
    query: Any,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Any:
    """
    Applies pagination (limit and offset) to a SQLAlchemy query.

    Args:
        query (Any): SQLAlchemy query object.
        limit (Optional[int]): Maximum number of records to return.
        offset (Optional[int]): Number of records to skip.

    Returns:
        Any: Query object with applied pagination.
    """
    try:
        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        return query

    except SQLAlchemyError as e:
        logger.error(f"Error applying pagination: {e}")
        raise

def apply_options(
    query: Any,
    options: Optional[List] = None,
) -> Any:
    """
    Applies Options to a SQLAlchemy query.

    Args:
        query (Any): SQLAlchemy query object.
        options (Optional[List]): List of query options
        
    Returns:
        Any: Query object with applied pagination.
    """
    try:
        if options is not None:
            return query.options(*options)

        return query

    except SQLAlchemyError as e:
        logger.error(f"Error applying options: {e}")
        raise
    
def get_fields_for_model(model: Type, fields_needed: Optional[List[str]] = None):
    """
    Extracts only the required fields from a model and validates them.
    
    Args:
        model (Type): The SQLAlchemy model.
        fields_needed (Optional[List[str]]): List of needed fields.

    Returns:
        List: List of SQLAlchemy model attributes (validated fields).
    """
    # Get all available fields from the model
    all_fields = {field: getattr(model, field) for field in model.__table__.columns.keys()}  

    # If `fields_needed` is None or empty, return all fields
    if not fields_needed:
        return list(all_fields.values()) 

    # Validate that `fields_needed` exists in `all_fields`
    valid_fields = [all_fields[field] for field in fields_needed if field in all_fields]

    if not valid_fields:
        raise ValueError(f"No valid fields found in {model.__tablename__} for fields: {fields_needed}")

    return valid_fields

def fetch_related_data(
    foreign_data: Dict[str, Any],
    foreign_pks: List[Any],
    depth: int = 0,
    max_depth: int = 5
) -> Dict[str, Any]:
    """
    Fetches related foreign data recursively, applying depth limit.

    Args:
        db (Session): SQLAlchemy session.
        foreign_data (Dict[str, Any]): Dictionary defining foreign key relationships.
        foreign_pks (List[Any]): Foreign keys to fetch related data for.
        depth (int): Current recursion depth.
        max_depth (int): Maximum allowed recursion depth.

    Returns:
        Dict[str, Any]: Dictionary of foreign data with primary key as key.

    Raises:
        ValueError: If recursion depth exceeds the maximum allowed.
    """
    if depth > max_depth:
        raise ValueError("Maximum recursion depth reached, possible circular dependency.")
    
    related_data = {}
    for fk, details in foreign_data.items():
        try:
            foreign_pk = details.get("pk", 'id')
            foreign_db = details["db"]
            foreign_model = details["model"]
            foreign_schema = details["response_schema"]
            foreign_soft_delete = details.get("soft_delete_condition", None)
            fields_needed = details.get("fields_needed", [foreign_model])
            nested_foreign_data = details.get("foreign_data", {})
            
            # Validate if `foreign_pk` exists in foreign model
            if foreign_pk not in foreign_model.__table__.columns.keys():
                logger.error(f"Invalid primary key {foreign_pk} for table {foreign_model.__tablename__}")
                raise ValueError(f"Invalid primary key {foreign_pk} for table {foreign_model.__tablename__}")
            
            # Fetch foreign data
            valid_fields = get_fields_for_model(foreign_model, fields_needed)
            field_options = [load_only(*valid_fields)]
            
            query_conditions = foreign_model.__table__.c[foreign_pk].in_(foreign_pks)
            
            foreign_results = get_list(
                db=foreign_db,
                model=foreign_model,
                response_schema=foreign_schema,
                soft_delete_condition=foreign_soft_delete,
                conditions=query_conditions,
                options=field_options,
                foreign_data=nested_foreign_data
            )
            related_data[fk] = {item[foreign_pk]: item for item in foreign_results["rows"]}

        except Exception as e:
            logger.error(f"Error fetching related data for foreign key {fk}. error: {e}")
            raise

    return related_data

def extract_foreign_keys(
    rows: Any, 
    foreign_data: Dict[str, Dict[str, Any]],
    ) -> Tuple[Any]:
    # Initialize a dictionary to store the unique foreign key values
    foreign_pks = {}

    # Handle single row or multiple rows input
    if not isinstance(rows, list):
        rows = [rows]  # Convert to list if it's a single row

    if len(rows) == 0:
        return foreign_pks
    
    # Iterate through the rows
    for row in rows:
        for fk, details in foreign_data.items():
            # Get the foreign key value from the row
            fk_value = getattr(row, fk, None)

            if fk_value:
                # If the foreign key value exists, add it to the set
                if fk not in foreign_pks:
                    foreign_pks[fk] = set()
                foreign_pks[fk].add(fk_value)

    return tuple(foreign_pks[fk])

def merge_foreign_keys(
    rows: Any, 
    foreign_data: Dict[str, Dict[str, Any]],
    related_data: Dict[str, Dict[str, Any]],
    ) -> Any:
    """
    Merges related foreign key data into the rows.

    Args:
        rows (list): List of row objects.
        foreign_data (dict): Dictionary with foreign key field names and their model details.
        related_data (dict): Dictionary containing the related data for each foreign key.

    Returns:
        Any: rows
    Raises:
        HTTPException: If foreign data is missing for a foreign key value.
    """
    for row in rows:
        for fk, details in foreign_data.items():
            fk_value = getattr(row, fk, None)
            foreign_table_name = details["model"].__tablename__  # Extract the table name

            if fk_value and fk_value in related_data.get(fk, {}):
                # Merge related foreign data into the row
                setattr(row, foreign_table_name, related_data[fk][fk_value])
            else:
                # Log error and raise HTTPException if data is missing
                logger.error(f"Foreign data is missing for foreign key {fk} with value {fk_value}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Foreign data is missing for foreign key {fk} with value {fk_value}"
                )
    return rows

def check_foreign_keys_exist(
    foreign_data: Dict[str, Dict[str, Any]],
    update_data: Dict[str, Any]
) -> None:
    """
    Check if all foreign key relations exist in the database efficiently.

    Args:
        foreign_data (Dict[str, Dict[str, Any]]): Mapping of foreign key fields to related models and database sessions.
        update_data (Dict[str, Any]): The data to update, containing foreign key fields and values.

    Raises:
        HTTPException: 404 if any related record does not exist.
    """
    missing_foreign_keys = []

    for fk_field, fk_details in foreign_data.items():
        related_db: Session = fk_details.get('db')
        related_model = fk_details.get('model')
        related_pk_field = fk_details.get('pk', 'id')  # Default to 'id' if pk is not specified
        fk_value = update_data.get(fk_field)

        if fk_value is None:
            logger.warning(f"Update data missing field '{fk_field}'")
            missing_foreign_keys.append(fk_field)
            continue

        # Ensure related model is valid
        if not related_db or not related_model:
            raise HTTPException(status_code=500, detail=f"Foreign data configuration is invalid for field '{fk_field}'")

        # Optimize query: If multiple fk_values are found, use a batch query
        if isinstance(fk_value, list): 
            existing_records = (
                related_db.query(related_model)
                .filter(getattr(related_model, related_pk_field).in_(fk_value))
                .all()
            )
            found_values = {getattr(record, related_pk_field) for record in existing_records}

            missing_values = set(fk_value) - found_values
            if missing_values:
                missing_foreign_keys.append(f"{fk_field}: {missing_values}")

        else:
            related_record = (
                related_db.query(related_model)
                .filter(getattr(related_model, related_pk_field) == fk_value)
                .first()
            )

            if not related_record:
                missing_foreign_keys.append(f"{fk_field}: {fk_value}")

    # If there are missing foreign keys, raise an error
    if missing_foreign_keys:
        error_message = f"Missing foreign key references: {', '.join(missing_foreign_keys)}"
        logger.error(error_message)
        raise HTTPException(status_code=404, detail=error_message)

    logger.info("All foreign key checks passed successfully.")
               
def get_list(
    db: Session,
    model: Type,  
    response_schema: Type, 
    soft_delete_condition: Optional[Any] = None,  
    conditions: Optional[Any] = None, 
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    sort_field: str = 'id',
    sort_order_ascending: bool = False,
    options: Optional[List[Any]] = None,
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Fetch a paginated list of records with recursive foreign key resolution.

    Args:
        db (Session): SQLAlchemy session.
        model (Type): SQLAlchemy model.
        response_schema (Type): Pydantic response schema.
        soft_delete_condition (Optional[Any]): Soft delete condition filter.
        conditions (Optional[Any]): Additional filters.
        limit (Optional[int]): Number of records to fetch.
        offset (Optional[int]): Number of records to skip.
        sort_field (str): Field to sort by.
        sort_order_ascending (bool): Sort order (default descending).
        options (Optional[List[Any]]): SQLAlchemy ORM options.
        foreign_data (Optional[Dict[str, Dict[str, Any]]]): Nested foreign key relations.

    Returns:
        Dict[str, Any]: Dictionary containing fetched rows and total count.
    """
    try:  
        raw_query = db.query(model)
        query_with_options = apply_options(raw_query, options)
        query_filtered = apply_filters(query_with_options, soft_delete_condition, conditions)
        
        # Count total records before applying filters
        unfiltered_count_query = select(func.count()).select_from(model)
        logger.debug(
            "Executing count query for total_not_paginated: %s", 
            str(unfiltered_count_query.compile(compile_kwargs={"literal_binds": True})).replace("\n", " ")
            )
        total_not_paginated = db.scalar(unfiltered_count_query)

        # Count total records after filters and pagination
        filtered_count_query = select(func.count()).select_from(query_filtered.subquery())
        logger.debug(
            "Executing count query for total: %s", 
            str(filtered_count_query.compile(compile_kwargs={"literal_binds": True})).replace("\n", " ")
        )
        total = db.scalar(filtered_count_query)

        query = apply_pagination(
            apply_sorting(query_filtered, model, sort_field, sort_order_ascending), 
            limit, 
            offset
        )
        
        # Fetch records
        logger.debug(f"Executing query: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}".replace("\n", " "))
        rows = query.all()
                
        if not foreign_data:
            response_data = [response_schema.from_orm(row).model_dump() for row in rows]
            logger.debug(f"Fetched {model.__tablename__} ({len(response_data)} records)")
            return {
                "rows": response_data,
                "total": total,
                "totalNotFiltered": total_not_paginated,
            }
        
        # Collect unique foreign key values for filtering foreign data
        foreign_pks = extract_foreign_keys(rows, foreign_data)
        
        # Fetch related foreign data (recursively)
        related_data = fetch_related_data(foreign_data, foreign_pks)
        
        # Merge foreign key data into response
        rows = merge_foreign_keys(rows, foreign_data, related_data)

        response_data = [response_schema.from_orm(row).model_dump() for row in rows]
        logger.debug(f"Fetched {model.__tablename__} ({len(response_data)} records)")
        
        return {
            "rows": response_data,
            "total": total,
            "totalNotFiltered": total_not_paginated,
        }

    except Exception as e:
        logger.error(f"Database error while fetching {model.__tablename__}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database error while fetching {model.__tablename__}: {str(e)}")

def get_item(
    db: Session,
    row_id: Any,
    model: Type,  
    response_schema: Type, 
    soft_delete_condition: Optional[Any] = None,  
    conditions: Optional[Any] = None, 
    options: Optional[List[ORMOption]] = None,
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Any:
    """
    Fetch a single item from the database, including foreign key relationships.

    Args:
        db (Session): SQLAlchemy database session.
        row_id (Any): The primary key of the row to fetch.
        model (Type): SQLAlchemy model class.
        response_schema (Type): Pydantic response schema.
        soft_delete_condition (Optional[Any]): Condition to exclude soft-deleted items.
        conditions (Optional[Any]): Additional filter conditions.
        options (Optional[List[ORMOption]]): ORM options like `joinedload`.
        foreign_data (Optional[Dict[str, Dict[str, Any]]]): Foreign key relationships for nested fetching.

    Returns:
        Any: Serialized response schema.

    Raises:
        HTTPException: 404 if not found, 503 on database error.
    """
    try:
        # Make query
        raw_query = db.query(model)
        query_with_options = apply_options(raw_query, options)
        query_filtered = apply_filters(query_with_options, soft_delete_condition, conditions)
        # Fetch the item by ID
        query_item = query_filtered.filter(model.id == row_id)
        query = query_item

        # Execute query
        logger.debug(f"Executing query: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}".replace("\n", " "))
        row = query.first()

        if not row:
            raise HTTPException(status_code=404, detail=f"{model.__tablename__.capitalize()} not found - id={row_id}")

        # If foreign_data is provided, fetch and merge related data
        if foreign_data:
            # Collect unique foreign key values for filtering foreign data
            foreign_pks = extract_foreign_keys([row], foreign_data)
            
            # Fetch related foreign data (recursively)
            related_data = fetch_related_data(foreign_data, foreign_pks)
            
            # Merge foreign key data into the row
            row = merge_foreign_keys([row], foreign_data, related_data)[0]

        return response_schema.from_orm(row).model_dump()

    except Exception as e:
        logger.exception(f"Database error while fetching {model.__tablename__} item {row_id}: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database error while fetching {model.__tablename__} item {row_id}. error: {str(e)}")
    
def update_item(
    db: Session,
    row_id: Any,
    model: Type,
    new_data: Dict[str, Any],
    response_schema: Type,
    soft_delete_condition: Optional[Any] = None,
    conditions: Optional[Any] = None,
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None,
    options: Optional[List[ORMOption]] = None,
) -> Any:
    """
    Update an existing item in the database, including foreign key relationships.

    Args:
        db (Session): SQLAlchemy database session.
        row_id (Any): The primary key of the row to fetch.
        model (Type): SQLAlchemy model class.
        new_data (Dict[str, Any]): Dictionary containing fields to update and their new values.
        response_schema (Type): Pydantic response schema.
        soft_delete_condition (Optional[Any]): Condition to exclude soft-deleted items.
        conditions (Optional[Any]): Additional filter conditions.
        options (Optional[List[ORMOption]]): ORM options like `joinedload`.
        foreign_data (Optional[Dict[str, Dict[str, Any]]]): Foreign key relationships for nested fetching.

    Returns:
        Any: Serialized response schema with the updated item.

    Raises:
        HTTPException: 404 if not found, 400 for invalid fields, 503 on database error.
    """
    row = None
    try:
        # Make query
        raw_query = db.query(model)
        query_with_options = apply_options(raw_query, options)
        query_filtered = apply_filters(query_with_options, soft_delete_condition, conditions)
        # Fetch the item by ID
        query_item = query_filtered.filter(model.id == row_id)
        query = query_item
        
        row = query.first()

        # If the item is not found, raise an HTTPException
        if not row:
            raise HTTPException(status_code=404, detail=f"{model.__tablename__.capitalize()} not found - id={row_id}")

        # Check if all foreign data exists
        if foreign_data:
            check_foreign_keys_exist(foreign_data, new_data.model_dump())

        # Apply the updates to the record
        for field, value in new_data.model_dump().items():
            if hasattr(row, field):
                setattr(row, field, value)
            else:
                raise HTTPException(status_code=400, detail=f"Invalid field: {field}")

        # If foreign_data is provided, merge related foreign key data
        if foreign_data:
            # Collect unique foreign key values for filtering foreign data
            foreign_pks = extract_foreign_keys([row], foreign_data)
            # Fetch related foreign data (recursively)
            related_data = fetch_related_data(foreign_data, foreign_pks)
            # Merge foreign key data into the row
            row = merge_foreign_keys([row], foreign_data, related_data)[0]
            
        
        # Commit the changes to the database
        db.commit()
        
        # Serialize the updated row
        updated_data = response_schema.from_orm(row).model_dump()

        return updated_data

    except IntegrityError as e:
        db.rollback()
        error_message = f"Integrity error while updating {model.__tablename__} item {str(row_id)}: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)
        
    except Exception as e:
        db.rollback()
        error_message = f"Error updating {model.__tablename__} item {str(row_id)}: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=503, detail=error_message)
     
def create_item(
    db: Session,
    model: Type,
    response_schema: Type,
    create_data: Dict[str, Any],
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None
) -> Any:
    """
    Creates a new item in the database, ensuring all foreign keys are valid before inserting.

    Args:
        db (Session): SQLAlchemy session.
        model (Type): SQLAlchemy model class.
        response_schema (Type): Pydantic response schema for the returned data.
        create_data (Dict[str, Any]): The data to insert into the new record.
        foreign_data (Optional[Dict[str, Dict[str, Any]]]): Optional dictionary of foreign key relationships.

    Returns:
        Any: The inserted item, serialized with the response schema.
    
    Raises:
        HTTPException: If any foreign key does not exist or there is an issue inserting the item.
    """
    try:
        # Check if foreign keys exist (if any)
        if foreign_data:
            check_foreign_keys_exist(foreign_data, create_data.model_dump())
        
        # Create the model instance from the provided data
        new_item = model(**create_data.model_dump())
        
        # Add the new item to the session
        db.add(new_item)
        db.commit()  # Commit to save the new item
        
        # Refresh the new item to get its ID or any other auto-generated fields
        db.refresh(new_item)
        
        # If foreign_data is provided, merge related foreign key data
        if foreign_data:
            # Collect unique foreign key values for filtering foreign data
            foreign_pks = extract_foreign_keys([new_item], foreign_data)

            # Fetch related foreign data (recursively)
            related_data = fetch_related_data(foreign_data, foreign_pks)

            # Merge foreign key data into the row
            row = merge_foreign_keys([new_item], foreign_data, related_data)[0]
            
        # Return the inserted data serialized with the response schema
        return response_schema.from_orm(row)
    
    except IntegrityError as e:
        # Handle any database integrity errors (e.g., violation of unique constraints)
        db.rollback()  # Rollback the transaction to prevent any partial updates
        error_message = "Database Integrity Error: " + str(e.orig)
        logger.error(error_message)
        raise HTTPException(status_code=400, detail=error_message)
    
    except Exception as e:
        # General exception handler for any other errors
        db.rollback()
        error_message = "Error creating item: " + str(e)
        logger.error(error_message)
        raise HTTPException(status_code=500, detail=error_message)
  
def delete_item(
    db: Session,
    row_id: Any,
    model: Type,
    options: Optional[List[ORMOption]] = None,
    soft_delete_field: Optional[str] = None,
    soft_delete_value: Optional[Any] = None,
) -> Dict:
    """
    Delete an item from the database. Supports both soft and hard delete.

    Args:
        db (Session): SQLAlchemy database session.
        row_id (Any): The primary key of the row to delete.
        model (Type): SQLAlchemy model class.
        soft_delete_field (Optional[str]): The field name for soft delete (e.g., 'is_deleted').
        soft_delete_value (Optional[Any]): The value to mark as deleted (e.g., True or 1).

    Raises:
        HTTPException: 404 if not found, 503 on database error.
    """
    try:
        # Make query
        raw_query = db.query(model)
        query_with_options = apply_options(raw_query, options)
        # Fetch the item by ID
        query_item = query_with_options.filter(model.id == row_id)
        query = query_item
        
        row = query.first()

        # If the item is not found, raise an HTTPException
        if not row:
            raise HTTPException(status_code=404, detail=f"{model.__tablename__.capitalize()} not found - id={row_id}")
        
        # If `soft_delete_field` is provided, perform a soft delete
        if soft_delete_field and soft_delete_value is not None:
            setattr(row, soft_delete_field, soft_delete_value)
            db.commit()
            return
        
        # If no soft delete, perform hard delete
        db.delete(row)
        db.commit()
        
        return {}

    except Exception as e:
        db.rollback()
        error_message = f"Error deleting {model.__tablename__} item {row_id}: {str(e)}"
        logger.error(error_message)
        raise HTTPException(status_code=503, detail=error_message)
