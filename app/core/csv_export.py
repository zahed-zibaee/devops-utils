import io
import csv
import pytz
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy.orm.interfaces import ORMOption  
from typing import Type, List, Any, Optional, Dict
from app.core.logging import logger
from app.core.crud import get_list


def export_to_csv(
    db: Session,
    model: Type,
    response_schema: Type,
    soft_delete_condition: Any,
    domain: str,
    export_file_prepend: str,
    sort_field: str = None,
    remove_unwanted_fields: List[str] = [],
    options: Optional[List[ORMOption]] = [],
    foreign_data: Optional[Dict[str, Dict[str, Any]]] = None,
    encoding: str = 'utf-8-sig',
    dialect: str = 'excel',
) -> StreamingResponse:
    """
    Generic function to export data from any table to a CSV file.

    Args:
        db (Session): SQLAlchemy session.
        model (Type): SQLAlchemy model.
        response_schema (Type): Pydantic response schema.
        soft_delete_condition (Any): Condition for soft-deleted rows.
        domain (str): Domain name for logging and error messages.
        export_file_prepend (str): Prefix for the exported CSV filename.
        remove_unwanted_fields (List[str]): List of fields to exclude from the CSV.
        options (Optional[List[ORMOption]]): ORM options for eager loading.
        encoding (str): Encoding for the CSV file (default: 'utf-8-sig').
        dialect (str): CSV dialect (default: 'excel').

    Returns:
        StreamingResponse: CSV file as a streaming response.

    Raises:
        HTTPException: 503 if an error occurs during export.
    """
    try:
        # Fetch data from the database
        rows = get_list(
            db=db,
            model=model,
            sort_field=sort_field,
            response_schema=response_schema,
            soft_delete_condition=soft_delete_condition,
            options=options,
            foreign_data=foreign_data,
        )

        # Generate the CSV file
        tz = pytz.timezone('Asia/Tehran')
        date_time = datetime.now(tz).strftime('%Y%m%d%H%M')

        # Determine fieldnames from the response schema
        fieldnames = list(response_schema.schema()['properties'].keys())
        filtered_fieldnames = [field for field in fieldnames if field not in remove_unwanted_fields]

        # Write CSV data to a buffer
        strbuff = io.StringIO()
        writer = csv.DictWriter(strbuff, fieldnames=filtered_fieldnames, dialect=dialect)
        writer.writeheader()
        writer.writerows(rows['rows'])

        # Encode the CSV content
        csv_content = strbuff.getvalue().encode(encoding)
        strbuff.close()

        # Return the CSV file as a streaming response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={export_file_prepend}_{date_time}.csv"}
        )

    except Exception as e:
        logger.exception(f"Failed to export {domain} CSV: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Failed to export {domain} CSV: {str(e)}")
    
    
    
    
    