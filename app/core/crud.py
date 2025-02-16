# app/core/crud.py
from typing import List, Dict, Any, Type, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException

from app.core.logging import logger


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
) -> Dict[str, Any]:
    """
    Generic function to fetch a list of records from any table.
    """
    try:
        # Base query with soft delete condition
        query = db.query(model)
        if soft_delete_condition is not None:
            query = query.filter(soft_delete_condition)

        # Apply predefined conditions if provided
        if conditions is not None:
            query = query.filter(conditions)

        # Count total records (before pagination)
        total_not_filtered = query.count()

        # Sort 
        if sort_field and hasattr(model, sort_field):
            column = getattr(model, sort_field)
            query = query.order_by(column.asc() if sort_order_ascending else column.desc())
            
        # Apply pagination
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        # Fetch records
        rows = query.all()

        # Convert rows to response schema
        response_data = [response_schema.model_validate(row).model_dump() for row in rows]

        logger.debug(f'Fetched {model.__tablename__}: {str(response_data[:5])} ...')
        return {
            "rows": response_data,
            "total": total_not_filtered,
            "totalNotFiltered": total_not_filtered,
        }
    except Exception as e:
        logger.exception(f"Database error while fetching {model.__tablename__} list. error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database error while fetching {model.__tablename__} list. error: {str(e)}")
    
def update_item(
    row_id: int,
    new_data: Any, 
    db: Session,
    model: Type,
    domain: str,
    soft_delete_condition: Optional[Any] = None,  
) -> Any:
    """
    Generic function to update a row in any table.
    """
    try:
        # Fetch the row to update
        row = db.query(model).filter(and_(model.id == row_id, soft_delete_condition)).first()
        if not row:
            logger.error(f"{domain.capitalize()} not found - id={row_id}")
            raise HTTPException(status_code=404, detail=f"{domain.capitalize()} not found - id={row_id}")

        for key, value in new_data.model_dump().items():
            setattr(row, key, value)

        # Commit changes to the database
        db.commit()
        db.refresh(row)
        return row
    except Exception as e:
        db.rollback()
        logger.exception(f"An error occurred while updating the {domain}.", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")