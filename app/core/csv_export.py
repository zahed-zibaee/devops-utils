import io
import csv
import pytz
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from typing import Type, List, Any
from app.core.logging import logger
from app.core.crud import get_list

def export_to_csv(
    db: Session,
    model: Type,  
    response_schema: Type,
    soft_delete_condition: Any,  
    domain: str, 
    export_file_prepend: str,  
    remove_unwanted_fields: List[str] = [],
):
    """
    Generic function to export data from any table to a CSV file.
    """
    try:
        # Fetch data from the database
        rows = get_list(
            db=db,
            model=model,
            response_schema=response_schema,
            soft_delete_condition=soft_delete_condition,
        )

        # Generate the CSV file
        tz = pytz.timezone('Asia/Tehran')
        date_time = datetime.now(tz).strftime('%Y%m%d%H%M')
        
        strbuff = io.StringIO()
        fieldnames = [column.name for column in model.__table__.columns]
        filtered_fieldnames = [field for field in fieldnames if field not in remove_unwanted_fields]
        
        writer = csv.DictWriter(strbuff, fieldnames=filtered_fieldnames)
        writer.writeheader()
        
        writer.writerows([row for row in rows['rows']])

        csv_content = strbuff.getvalue().encode('utf-8-sig')
        strbuff.close()

        # Return the CSV file as a streaming response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={export_file_prepend}_{date_time}.csv"}
        )
    except Exception as e:
        logger.exception(f"Failed to export {domain} CSV")
        raise HTTPException(status_code=503, detail=f"Failed to export {domain} CSV")
    
    
    
    
    
    
    