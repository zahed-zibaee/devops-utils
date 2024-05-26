from typing import Union, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class BaseJsonLogSchema(BaseModel):
    """
    Main log in JSON format
    """
    thread: Union[int, str]
    level_name: str
    message: str
    source_log: str
    timestamp: str = Field(..., alias='@timestamp')
    app_name: str
    app_env: str
    duration: int
    exceptions: Union[List[str], str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class RequestJsonLogSchema(BaseModel):
    """
    Schema for request/response answer
    """
    request_uri: str
    request_referer: str
    request_method: str
    request_path: str
    request_host: str
    request_size: int
    request_content_type: str
    request_headers: dict
    request_body: Optional[str]
    request_direction: str
    response_status_code: int
    response_size: int
    response_headers: dict
    response_body: Optional[str]
    duration: int

    @field_validator('request_body', 'response_body', mode='before')
    def valid_body(cls, value, info):
        if isinstance(value, bytes):
            try:
                value = value.decode()
            except UnicodeDecodeError:
                value = 'file_bytes'
        return value